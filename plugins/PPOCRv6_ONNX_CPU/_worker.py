"""Worker: local inference only; never imports the installer."""
import base64
import importlib
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from _runtime import prepare

def main():
    protocol = sys.stdout
    sys.stdout = sys.stderr
    for stream in (protocol, sys.stderr):
        if hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8',errors='replace')
    if len(sys.argv)!=2 or sys.argv[1] not in ('ppocr_backend','lpr_backend','captcha_backend'):
        raise ValueError('Invalid backend')
    prepare(ROOT)
    api = None
    global_args = None
    for line in sys.stdin:
        rid = None
        try:
            req = json.loads(line)
            rid = req.get('id')
            op = req.get('op')
            if op == 'start':
                new_global = req.get('global_args') or {}
                if api is None or new_global != global_args:
                    if api:
                        api.stop()
                    api = importlib.import_module(sys.argv[1]).Api(new_global)
                    global_args = new_global
                error = api.start(req.get('local_args') or {})
                if error:
                    raise RuntimeError(error)
                result = {'started':True}
            elif op == 'run':
                if api is None:
                    raise RuntimeError('Engine not started')
                result = api.runBytes(base64.b64decode(req['image'],validate=True))
            elif op == 'stop':
                if api:
                    api.stop()
                return 0
            else:
                raise ValueError('Invalid operation')
            reply = {'id':rid,'ok':True,'result':result}
        except Exception as exc:
            reply = {'id':rid,'ok':False,'error':str(exc)+'\n'+traceback.format_exc()}
        protocol.write('@UMI_OCR_RPC@'+json.dumps(reply,ensure_ascii=True)+'\n')
        protocol.flush()
    if api:
        api.stop()
    return 0

if __name__=='__main__':
    sys.exit(main())
