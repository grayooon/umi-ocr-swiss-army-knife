"""Local, standard-library inventory. Never uploads; never imports third-party code."""
import hashlib
import json
from pathlib import Path
import platform
import struct
import sys

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main():
    root=Path(__file__).resolve().parent.parent
    if root.name not in ('PPOCRv6_ONNX_CPU','HyperLPR3_Plate_CPU','DDDDOCR_Captcha_Umi'):
        value=input('Drag ONE installed plugin folder here: ').strip().strip('"')
        root=Path(value).resolve()
    if not (root/'site-packages').is_dir():
        raise RuntimeError('Choose an installed plugin folder containing site-packages')
    packages=[]
    for info in sorted((root/'site-packages').glob('*.dist-info/METADATA')):
        d={}
        for line in info.read_text(encoding='utf-8',errors='replace').splitlines():
            for key in ('Name','Version','Requires-Python'):
                if line.startswith(key+': '):d[key]=line[len(key)+2:]
        packages.append(d)
    files=[]
    for path in sorted(root.rglob('*')):
        rel=path.relative_to(root)
        if any(p in ('_downloads','site-packages.previous','__pycache__') for p in rel.parts):continue
        if path.is_file() and path.suffix.lower() in ('.pyd','.dll','.onnx'):
            files.append({'path':rel.as_posix(),'size':path.stat().st_size,'sha256':sha(path)})
    result={'plugin':root.name,'os':platform.system(),'release':platform.release(),
            'version':platform.version(),'python':platform.python_version(),
            'pointer_bits':struct.calcsize('P')*8,'packages':packages,'files':files,
            'note':'Local inventory only; not an inference test or malware certificate. No computer/user name or absolute path collected.'}
    output=root/'environment-report.json'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Saved locally: '+str(output))
    print('Attach it manually only if you want to share it. No upload was performed.')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('[FAIL]',str(exc));sys.exit(1)
