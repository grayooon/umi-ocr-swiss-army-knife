"""Explicit, HTTPS-only setup. Never called by the OCR runtime.

Only pinned wheels are extracted; no get-pip, setup.py, shell or .pth execution.
The lock file is the trust anchor shipped in the source release.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import ssl
import struct
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

PLUGIN = Path(__file__).resolve().parent.parent
LOCK = Path(__file__).resolve().with_name('assets.lock.json')

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def validate_url(url):
    p = urllib.parse.urlsplit(url)
    host = (p.hostname or '').lower()
    permitted = host in ('files.pythonhosted.org', 'huggingface.co', 'raw.githubusercontent.com') or host.endswith('.huggingface.co') or host.endswith('.hf.co') or host.endswith('.xethub.hf.co')
    if p.scheme != 'https' or not permitted or p.username or p.password:
        raise ValueError('Unapproved download URL: ' + url)

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def obtain(asset, offline=False):
    sha = asset['sha256']
    if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
        raise ValueError('Invalid SHA-256 in lock')
    cache = PLUGIN / '_downloads'
    cache.mkdir(exist_ok=True)
    target = cache / sha
    if target.is_file() and digest(target) == sha:
        return target
    if offline:
        raise RuntimeError('Offline cache missing/corrupt: ' + asset.get('filename',asset.get('path','')))
    validate_url(asset['url'])
    print('GET ' + asset['url'], flush=True)
    opener = urllib.request.build_opener(SafeRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    req = urllib.request.Request(asset['url'], headers={'User-Agent':'UmiOCR-community-setup/1.1'})
    part = target.with_suffix('.part')
    try:
        with opener.open(req, timeout=90) as response, part.open('wb') as out:
            validate_url(response.geturl())
            size = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > asset['size']:
                    raise ValueError('Downloaded data exceeds pinned size')
                out.write(chunk)
        if size != asset['size'] or digest(part) != sha:
            raise ValueError('SHA-256 or file size mismatch; no installation performed')
        os.replace(str(part), str(target))
        return target
    finally:
        if part.exists():
            part.unlink()

def safe_parts(name):
    # ZIP uses forward slashes. Reject Windows drives, ADS, traversal and symlinks.
    if '\\' in name or ':' in name or name.startswith('/'):
        raise ValueError('Unsafe archive path: ' + name)
    parts = PurePosixPath(name).parts
    if not parts or '..' in parts:
        raise ValueError('Unsafe archive path: ' + name)
    return parts

def extract_wheel(archive, target):
    with zipfile.ZipFile(archive) as z:
        total = 0
        seen = set()
        for member in z.infolist():
            parts = safe_parts(member.filename)
            if ((member.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError('Symlink in wheel')
            total += member.file_size
            if total > 1024 * 1024 * 1024:
                raise ValueError('Wheel uncompressed size is too large')
            # PEP 427: relocate purelib/platlib. Keep other wheel data as data.
            if parts[0].endswith('.data') and len(parts) > 2 and parts[1] in ('purelib','platlib'):
                parts = parts[2:]
            dest = target.joinpath(*parts)
            key = str(dest).casefold()
            if key in seen and not member.is_dir():
                raise ValueError('Duplicate archive target')
            seen.add(key)
            if member.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as fi, dest.open('wb') as fo:
                    shutil.copyfileobj(fi, fo)

def install_wheels(assets, offline=False):
    # Fetch and check everything before touching the existing dependency folder.
    paths = [(a, obtain(a, offline)) for a in assets]
    stage = Path(tempfile.mkdtemp(prefix='_deps_stage_', dir=str(PLUGIN)))
    target = PLUGIN / 'site-packages'
    backup = PLUGIN / 'site-packages.previous'
    try:
        for a, path in paths:
            print('Extract: ' + a['filename'], flush=True)
            extract_wheel(path, stage)
        if target.exists():
            if backup.exists():
                raise RuntimeError('site-packages.previous already exists; keep a backup elsewhere before retrying')
            target.rename(backup)
        try:
            stage.rename(target)
        except Exception:
            if backup.exists() and not target.exists():
                backup.rename(target)
            raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)

def install_models(assets, offline=False):
    for a in assets:
        parts = safe_parts(a['path'])
        dest = PLUGIN / 'models'
        dest = dest.joinpath(*parts)
        if dest.is_file() and digest(dest) == a['sha256']:
            print('Verified existing model: ' + a['path'])
            continue
        cached = obtain(a, offline)
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + '.part')
        shutil.copyfile(cached, part)
        os.replace(str(part), str(dest))

def main():
    parser = argparse.ArgumentParser(description='Pinned offline OCR plugin setup')
    parser.add_argument('--action', choices=['all','deps','models','list'],default='all')
    parser.add_argument('--tier', choices=['small','tiny','medium','all'],default='small')
    parser.add_argument('--offline',action='store_true',help='Use checked _downloads cache without network')
    args = parser.parse_args()
    manifest = json.loads(LOCK.read_text(encoding='utf-8'))
    if args.action == 'list':
        print(json.dumps(manifest,ensure_ascii=False,indent=2))
        return 0
    if os.name != 'nt' or sys.version_info[:2] != (3,8) or struct.calcsize('P') != 8:
        raise RuntimeError('Requires Umi-OCR Windows CPython 3.8 x64. Do not use the system Python.')
    if args.action in ('all','deps') and sys.getwindowsversion()[:2] <= (6,1):
        raise RuntimeError('The pinned official ONNX Runtime DLL imports a Windows 8+ API. Win7 dependency downloads are blocked in this candidate. Keep your existing dependencies for maintainer hardware tests; no verified Win7 bundle is included. Existing files have NOT been changed. See README.md.')
    print('Plugin: ' + str(PLUGIN))
    print('Close Umi-OCR including its tray icon before setup. No administrator rights needed.')
    if args.action in ('all','deps'):
        install_wheels(manifest['wheels'],args.offline)
    if args.action in ('all','models'):
        models=[a for a in manifest['models'] if args.tier=='all' or a.get('tier',args.tier)==args.tier]
        install_models(models,args.offline)
        # ddddocr 1.5.6 embeds both original weights in its official wheel.
        if manifest['plugin']=='DDDDOCR_Captcha_Umi':
            for name in ('common.onnx','common_old.onnx'):
                if not (PLUGIN/'site-packages'/'ddddocr'/name).is_file():
                    raise RuntimeError('ddddocr model missing; run 01_setup_online.bat first')
    print('Files installed. Run 02_self_check.bat. Installation success does NOT mean inference tests passed.')
    return 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('[FAIL] '+str(exc),file=sys.stderr)
        sys.exit(1)
