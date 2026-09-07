"""Make source/plugin release archives. Excludes local binaries, images and logs."""
import hashlib
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parent.parent
SKIP={'dist','.git','__pycache__','site-packages','site-packages.previous','models','_downloads','_pip_boot','pipboot'}
EXTENSIONS={'.py','.bat','.md','.json','.csv','.txt','.yml','.yaml','.html'}
NAMES={'LICENSE','NOTICE','.gitignore','.gitattributes'}

def source_files(base):
    for path in sorted(base.rglob('*')):
        relative=path.relative_to(base)
        if any(p in SKIP or p.startswith('_deps_stage_') for p in relative.parts):continue
        if path.is_symlink():raise RuntimeError('Symlink not allowed: '+str(relative))
        if path.is_file() and path.name not in ('environment-report.json','audit-local-results.json'):
            if path.suffix in EXTENSIONS or path.name in NAMES:yield path

def main():
    version=(ROOT/'VERSION.txt').read_text().strip()
    if not version or any(c not in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-' for c in version):
        raise ValueError('Invalid version')
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    targets=[('umi-ocr-swiss-army-knife-source',ROOT)]+[(p.name,p) for p in sorted((ROOT/'plugins').iterdir()) if p.is_dir()]
    hashes=[]
    for name,base in targets:
        target=out/(name+'-v'+version+'.zip')
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for path in source_files(base):
                archive.write(path,name+'/'+path.relative_to(base).as_posix())
        with zipfile.ZipFile(target) as archive:
            bad=archive.testzip()
            if bad:raise RuntimeError('Corrupt archive: '+bad)
        hashes.append(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name)
        print('Created:',target.name)
    (out/'SHA256SUMS.txt').write_text('\n'.join(hashes)+'\n',encoding='ascii')
    print('Archives contain source + installers, not preinstalled dependencies/models.')
    return 0

if __name__=='__main__':sys.exit(main())
