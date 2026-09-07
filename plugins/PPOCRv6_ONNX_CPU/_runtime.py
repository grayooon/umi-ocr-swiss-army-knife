"""Load only this plugin's dependencies; retain DLL directory handles."""
import os
from pathlib import Path
import sys

_DLL_HANDLES = []
_PREPARED = False

def _block_python_network(event,args):
    # Defence in depth for Python modules, NOT an OS-level native DLL firewall.
    if event in ('socket.connect','socket.connect_ex','socket.bind','socket.getaddrinfo'):
        raise RuntimeError('Network is disabled during OCR inference')

def prepare(plugin):
    global _PREPARED
    if _PREPARED:
        return
    site = Path(plugin) / 'site-packages'
    if not site.is_dir():
        raise RuntimeError('Missing site-packages. Run tools/01_setup_online.bat.')
    # Inserting a path does not execute arbitrary .pth startup files.
    sys.path.insert(0,str(site))
    dlls=[site/'onnxruntime'/'capi',site/'cv2',site/'numpy'/'.libs',site/'numpy.libs',site/'PIL']
    dlls=[str(p) for p in dlls if p.is_dir()]
    if os.name=='nt':
        os.environ['PATH'] = os.pathsep.join(dlls+[os.environ.get('PATH','')])
        if hasattr(os,'add_dll_directory'):
            for p in dlls:
                try:
                    _DLL_HANDLES.append(os.add_dll_directory(p))
                except OSError:
                    # Win7 DLL-directory APIs depend on installed system updates.
                    pass
    sys.addaudithook(_block_python_network)
    import onnxruntime as ort
    ort.disable_telemetry_events()
    print('ORT=%s; file=%s; telemetry disabled; CPU inference' % (ort.__version__,ort.__file__))
    _PREPARED = True
