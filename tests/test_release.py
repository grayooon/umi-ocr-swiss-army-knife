"""Source/security regression tests. These do NOT certify Windows inference."""
import ast
import base64
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / 'plugins'
PP = PLUGINS / 'PPOCRv6_ONNX_CPU'

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

class ReleaseTests(unittest.TestCase):
    def test_python38_syntax(self):
        for path in ROOT.rglob('*.py'):
            if any(x in path.parts for x in ('site-packages','_downloads','dist')):
                continue
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path), feature_version=(3,8))

    def test_plugin_discovery_and_parent_isolation(self):
        code = '''import sys, types, importlib
sys.path.insert(0,sys.argv[1])
tr=types.ModuleType('plugin_i18n')
tr.Translator=lambda *a: (lambda s:s)
sys.modules['plugin_i18n']=tr
for name in ['PPOCRv6_ONNX_CPU','HyperLPR3_Plate_CPU','DDDDOCR_Captcha_Umi']:
 p=importlib.import_module(name)
 assert p.PluginInfo['group']=='ocr'
 api=p.PluginInfo['api_class']({})
 for method in ['start','stop','runPath','runBytes','runBase64']: assert callable(getattr(api,method))
 api.stop()
assert not any(n in sys.modules for n in ['numpy','cv2','PIL','ddddocr','onnxruntime'])
'''
        p=subprocess.run([sys.executable,'-c',code,str(PLUGINS)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)

    def test_identical_shared_runtime(self):
        for name in ['_bridge.py','_worker.py','_runtime.py','tools/setup.py','tools/self_check.py']:
            copies=[(p/name).read_bytes() for p in PLUGINS.iterdir() if p.is_dir()]
            self.assertTrue(all(x==copies[0] for x in copies))

    def test_relocated_models_ignore_working_directory(self):
        for relative,fn in [('ocr_engine/paths.py','default_search_dirs'),('lpr_engine/paths.py','search_dirs')]:
            plugin=PP if relative.startswith('ocr') else PLUGINS/'HyperLPR3_Plate_CPU'
            mod=module(plugin/relative,'path_test')
            dirs=getattr(mod,fn)('my models !')
            self.assertEqual(Path(dirs[0]),plugin/'my models !')

    def test_wheel_traversal_and_symlink_rejected(self):
        setup=module(PP/'tools/setup.py','installer_test')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for bad in ['../escape.py','/tmp/escape.py','C:/escape.py','pkg\\escape.py','pkg/file:stream']:
                z=root/'bad.whl'
                with zipfile.ZipFile(z,'w') as f:f.writestr(bad,'bad')
                with self.assertRaises(ValueError):setup.extract_wheel(z,root/'output')
            info=zipfile.ZipInfo('pkg/link');info.external_attr=0o120777 << 16
            with zipfile.ZipFile(root/'bad.whl','w') as f:f.writestr(info,'../target')
            with self.assertRaises(ValueError):setup.extract_wheel(root/'bad.whl',root/'output')

    def test_data_relocation_and_pth_not_executed(self):
        setup=module(PP/'tools/setup.py','installer_test')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);z=root/'ok.whl'
            with zipfile.ZipFile(z,'w') as f:
                f.writestr('demo.data/purelib/demo/__init__.py','value=1')
                f.writestr('demo.pth','import sys; raise RuntimeError("must not execute")')
            setup.extract_wheel(z,root/'out')
            self.assertTrue((root/'out/demo/__init__.py').is_file())

    def test_offline_hash_failure_keeps_existing_dependencies(self):
        setup=module(PP/'tools/setup.py','installer_test')
        with tempfile.TemporaryDirectory() as td:
            setup.PLUGIN=Path(td);(setup.PLUGIN/'site-packages').mkdir()
            marker=setup.PLUGIN/'site-packages/keep.txt';marker.write_text('existing')
            asset={'sha256':'0'*64,'filename':'bad.whl'}
            with self.assertRaises(RuntimeError):setup.install_wheels([asset],offline=True)
            self.assertEqual(marker.read_text(),'existing')

    def test_replace_keeps_previous_and_refuses_second_backup(self):
        setup=module(PP/'tools/setup.py','installer_test')
        with tempfile.TemporaryDirectory() as td:
            setup.PLUGIN=Path(td);(setup.PLUGIN/'site-packages').mkdir()
            (setup.PLUGIN/'site-packages/original.txt').write_text('old')
            archive=setup.PLUGIN/'source.whl'
            with zipfile.ZipFile(archive,'w') as f:f.writestr('demo.py','value=2')
            with mock.patch.object(setup,'obtain',return_value=archive):
                setup.install_wheels([{'filename':'demo.whl'}])
                self.assertTrue((setup.PLUGIN/'site-packages.previous/original.txt').is_file())
                with self.assertRaises(RuntimeError):setup.install_wheels([{'filename':'demo.whl'}])
                self.assertTrue((setup.PLUGIN/'site-packages/demo.py').is_file())

    def test_download_url_policy(self):
        setup=module(PP/'tools/setup.py','installer_test')
        for url in ['http://files.pythonhosted.org/a','https://files.pythonhosted.org.evil.example/a','file:///x','https://user:pass@huggingface.co/a']:
            with self.assertRaises(ValueError):setup.validate_url(url)
        setup.validate_url('https://raw.githubusercontent.com/owner/repo/commit/a')

    def test_no_image_is_not_success(self):
        p=subprocess.run([sys.executable,str(PP/'tools/self_check.py')],input='',capture_output=True,text=True)
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertIn('NOT tested',p.stdout)

    def test_python_network_guard(self):
        runtime=module(PP/'_runtime.py','runtime_test')
        for name in ['socket.connect','socket.bind','socket.getaddrinfo']:
            with self.assertRaises(RuntimeError):runtime._block_python_network(name,())
        runtime._block_python_network('open',())

    def test_real_process_protocol_with_fake_inference_backend(self):
        bridge_module=module(PP/'_bridge.py','bridge_test')
        with tempfile.TemporaryDirectory(prefix="Umi path ' ! ") as td:
            root=Path(td)
            shutil.copyfile(PP/'_worker.py',root/'_worker.py')
            (root/'_runtime.py').write_text('def prepare(root):\n print("Your argv: fake launcher diagnostic")\n',encoding='utf-8')
            (root/'ppocr_backend.py').write_text('''class Api:
 def __init__(self,args): self.count=0
 def start(self,args): self.count+=1; print('{"unframed":"ignore"}'); return ''
 def runBytes(self,data): return {'code':100,'data':[{'text':str(len(data)), 'count':self.count}]}
 def stop(self): pass
''',encoding='utf-8')
            api=bridge_module.Bridge(root,'ppocr_backend',{})
            # Windows production uses Umi runtime; tests explicitly choose test interpreter.
            api._python=lambda:sys.executable
            try:
                self.assertEqual(api.start({}),'')
                a=api.runBytes(b'abc')
                self.assertEqual(a['data'][0]['text'],'3')
                self.assertEqual(api.runBase64(base64.b64encode(b'abc')),a)
                img=root/'image.bin';img.write_bytes(b'abc')
                self.assertEqual(api.runPath(str(img)),a)
                self.assertEqual(api.start({}),'')
                self.assertEqual(api.runBytes(b'x')['data'][0]['count'],2)
                self.assertIn('Your argv',str(api.diagnostics))
                self.assertEqual(api.runBase64('!!!')['code'],103)
                process=api.process
            finally:api.stop()
            self.assertIsNotNone(process.poll())

    def test_timeout_is_reported(self):
        b=module(PP/'_bridge.py','bridge_timeout')
        api=b.Bridge(PP,'ppocr_backend',{})
        api._launch=lambda:None
        api.process=mock.Mock()
        api.responses=mock.Mock();api.responses.get.side_effect=queue.Empty
        with self.assertRaisesRegex(RuntimeError,'120 seconds'):api._rpc('start')
        api.process=None

    def test_windows_interpreter_is_runtime_not_umi_cli(self):
        b=module(PP/'_bridge.py','bridge_path')
        api=b.Bridge(PP,'ppocr_backend',{})
        with mock.patch.object(b.os,'name','nt'),mock.patch.object(Path,'is_file',return_value=True):
            self.assertEqual(api._python(),str(PP.parent.parent/'runtime/python.exe'))
        with mock.patch.object(b.os,'name','nt'),mock.patch.object(Path,'is_file',return_value=False):
            with self.assertRaises(RuntimeError):api._python()

if __name__=='__main__': unittest.main(verbosity=2)
