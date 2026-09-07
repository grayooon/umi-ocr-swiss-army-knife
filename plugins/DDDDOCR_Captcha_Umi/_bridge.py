"""Local stdio bridge. Imports only Python standard-library modules in Umi."""
import atexit
import base64
from collections import deque
import json
from pathlib import Path
import os
import queue
import subprocess
import sys
import threading
import time

PREFIX = '@UMI_OCR_RPC@'

def _reader(stream, responses, diagnostics):
    try:
        for line in iter(stream.readline, ''):
            if line.startswith(PREFIX):
                responses.put(line[len(PREFIX):])
            else:
                diagnostics.append(line.strip()[:400])
    except Exception as exc:
        diagnostics.append(str(exc))
    finally:
        responses.put(None)

class Bridge:
    def __init__(self, plugin, backend, global_args):
        self.plugin = Path(plugin).resolve()
        self.backend = backend
        self.global_args = global_args or {}
        self.local_args = {}
        self.process = None
        self.lock = threading.RLock()
        self.responses = None
        self.diagnostics = deque(maxlen=8)
        self.serial = 0
        self.started = False
        atexit.register(self.stop)

    def _python(self):
        path = self.plugin.parent.parent / 'runtime' / 'python.exe'
        if os.name == 'nt':
            if not path.is_file():
                raise RuntimeError('Cannot find Umi runtime Python: '+str(path))
            return str(path)
        # Development/tests only; Windows never falls back to Umi-OCR.exe.
        return sys.executable

    def _launch(self):
        if self.process and self.process.poll() is None:
            return
        self.stop()
        self.responses = queue.Queue()
        self.diagnostics.clear()
        self.process = subprocess.Popen(
            [self._python(), '-u', str(self.plugin / '_worker.py'), self.backend],
            cwd=str(self.plugin), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8',
            errors='replace', bufsize=1,
            creationflags=0x08000000 if os.name=='nt' else 0,
        )
        threading.Thread(target=_reader,args=(self.process.stdout,self.responses,self.diagnostics),daemon=True).start()

    def _rpc(self, op, **payload):
        self._launch()
        self.serial += 1
        request = dict(payload, id=self.serial, op=op)
        self.process.stdin.write(json.dumps(request,ensure_ascii=True)+'\n')
        self.process.stdin.flush()
        deadline = time.monotonic()+120
        while True:
            try:
                line = self.responses.get(timeout=max(0,deadline-time.monotonic()))
            except queue.Empty:
                raise RuntimeError('Worker exceeded 120 seconds; reduce image size or use a smaller model. '+' | '.join(self.diagnostics))
            if line is None:
                raise RuntimeError('Worker exited. '+' | '.join(self.diagnostics))
            result = json.loads(line)
            if result.get('id') != self.serial:
                continue
            if not result.get('ok'):
                raise RuntimeError(result.get('error','Worker failed'))
            return result['result']

    def start(self, args):
        with self.lock:
            self.local_args = args or {}
            try:
                self._rpc('start', global_args=self.global_args, local_args=self.local_args)
                self.started = True
                return ''
            except Exception as exc:
                self.stop()
                return '[Error] '+str(exc)

    def stop(self):
        with self.lock:
            p = self.process
            self.process = None
            self.started = False
            if p is None:
                return
            try:
                if p.poll() is None:
                    p.stdin.write(json.dumps({'op':'stop','id':-1})+'\n')
                    p.stdin.flush()
                    p.wait(timeout=3)
            except Exception:
                if p.poll() is None:
                    p.terminate()
                    try:
                        p.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait(timeout=2)
            finally:
                for stream in (p.stdin,p.stdout):
                    try:
                        stream.close()
                    except Exception:
                        pass

    def runPath(self,path):
        try:
            with open(path,'rb') as f:
                return self.runBytes(f.read())
        except Exception as exc:
            return {'code':103,'data':'[Error] '+str(exc)}

    def runBase64(self,data):
        try:
            text = data.decode('ascii') if isinstance(data,bytes) else str(data)
            if text.startswith('data:'):
                text = text.split(',',1)[1]
            return self.runBytes(base64.b64decode(text,validate=True))
        except Exception as exc:
            return {'code':103,'data':'[Error] '+str(exc)}

    def runBytes(self,data):
        with self.lock:
            try:
                if not isinstance(data,(bytes,bytearray,memoryview)):
                    raise ValueError('Image must be bytes')
                if not self.started or not self.process or self.process.poll() is not None:
                    error = self.start(self.local_args)
                    if error:
                        raise RuntimeError(error)
                return self._rpc('run',image=base64.b64encode(bytes(data)).decode('ascii'))
            except Exception as exc:
                self.stop()
                return {'code':104,'data':'[Error] '+str(exc)}
