"""Build isolated release bundles, or checksum/verify the ZIPs actually published.

Only the Python standard library is required (Python 3.8+).
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ('DDDDOCR_Captcha_Umi', 'HyperLPR3_Plate_CPU', 'PPOCRv6_ONNX_CPU')
SKIP = {'dist', '.git', '__pycache__', 'site-packages', 'site-packages.previous',
        'models', '_downloads', '_pip_boot', 'pipboot'}
EXTENSIONS = {'.py', '.bat', '.md', '.json', '.csv', '.txt', '.yml', '.yaml', '.html'}
NAMES = {'LICENSE', 'NOTICE', '.gitignore', '.gitattributes'}
MANIFEST = 'SHA256SUMS.txt'


def _walk_error(error):
    raise error


def source_files(base):
    files = []
    for current, directories, filenames in os.walk(str(base), topdown=True,
                                                  followlinks=False, onerror=_walk_error):
        # Prune before walking: installed dependencies and old bundles can be huge.
        directories[:] = sorted(name for name in directories
                                if name not in SKIP and not name.startswith('_deps_stage_'))
        for name in directories:
            path = Path(current) / name
            if path.is_symlink():
                raise RuntimeError('Symlink not allowed: ' + str(path.relative_to(base)))
        for name in filenames:
            if name in SKIP or name.startswith('_deps_stage_'):
                continue
            path = Path(current) / name
            if path.is_symlink():
                raise RuntimeError('Symlink not allowed: ' + str(path.relative_to(base)))
            if path.is_file() and name not in ('environment-report.json', 'audit-local-results.json'):
                if path.suffix in EXTENSIONS or name in NAMES:
                    files.append(path)
    yield from sorted(files)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def zip_files(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError('Release directory not found: ' + str(directory))
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() == '.zip')
    if not paths:
        raise ValueError('No ZIP files in: ' + str(directory))
    seen = set()
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError('Not a regular ZIP file: ' + path.name)
        if not re.fullmatch(r'[^/\\:\x00-\x1f\x7f-\x9f\u2028\u2029]+\.[zZ][iI][pP]', path.name):
            raise ValueError('Unsafe ZIP filename: ' + repr(path.name))
        if path.name.casefold() in seen:
            raise ValueError('Duplicate ZIP filename (case-insensitive): ' + path.name)
        seen.add(path.name.casefold())
    return paths


def write_checksums(directory):
    """Hash only the ZIP files present, without repacking or changing them."""
    directory = Path(directory)
    paths = zip_files(directory)
    manifest = directory / MANIFEST
    if manifest.is_symlink():
        raise ValueError('Symlink not allowed: ' + str(manifest))
    text = ''.join('{}  {}\n'.format(sha256(p), p.name) for p in paths)
    # Publish a complete manifest, never a half-written one.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         prefix='.SHA256SUMS-', dir=str(directory),
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(str(temporary), str(manifest))
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return manifest


def verify_checksums(directory):
    """Require an exact match: no missing, extra, duplicate or modified ZIPs."""
    directory = Path(directory)
    paths = {p.name: p for p in zip_files(directory)}
    manifest = directory / MANIFEST
    if manifest.is_symlink():
        raise ValueError('Symlink not allowed: ' + str(manifest))
    entries = {}
    seen = set()
    for number, line in enumerate(manifest.read_text(encoding='utf-8-sig').splitlines(), 1):
        match = re.fullmatch(r'([0-9a-fA-F]{64})  ([^/\\:\x00-\x1f\x7f-\x9f\u2028\u2029]+\.[zZ][iI][pP])', line)
        if not match:
            raise ValueError('Invalid checksum line {}'.format(number))
        digest, name = match.groups()
        if name.casefold() in seen:
            raise ValueError('Duplicate checksum filename: ' + name)
        seen.add(name.casefold())
        entries[name] = digest.lower()
    missing = sorted(set(entries) - set(paths))
    extra = sorted(set(paths) - set(entries))
    if missing or extra:
        raise ValueError('ZIP list mismatch; missing: {}; not listed: {}'.format(missing, extra))
    for name, expected in entries.items():
        if sha256(paths[name]) != expected:
            raise ValueError('SHA-256 mismatch: ' + name)
    return sorted(entries)


def release_version(root):
    version = (root / 'VERSION.txt').read_text(encoding='utf-8-sig').strip()
    if not re.fullmatch(r'[0-9][0-9a-zA-Z.-]*', version):
        raise ValueError('Invalid version')
    for name in PLUGINS:
        plugin = root / 'plugins' / name
        if plugin.is_symlink() or not plugin.is_dir():
            raise ValueError('Missing plugin or symlink: ' + name)
        plugin_version = (plugin / 'VERSION.txt').read_text(encoding='utf-8-sig').strip()
        if plugin_version != version:
            raise ValueError('Version mismatch: {} is {}, root is {}'.format(name, plugin_version, version))
    return version


def build_release(root, include_source=False):
    root = Path(root)
    version = release_version(root)
    out = root / 'dist'
    out.mkdir(exist_ok=True)
    if out.is_symlink():
        raise ValueError('Symlink not allowed: ' + str(out))
    # Every invocation owns a fresh bundle. Never merge with an older dist folder.
    stage = Path(tempfile.mkdtemp(prefix='.v' + version + '-', dir=str(out)))
    destination = out / stage.name[1:]
    try:
        targets = [(name, root / 'plugins' / name) for name in PLUGINS]
        if include_source:
            targets.append(('umi-ocr-swiss-army-knife-source', root))
        for name, base in targets:
            target = stage / (name + '-v' + version + '.zip')
            files = list(source_files(base))
            if not files:
                raise ValueError('No source files for: ' + name)
            with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for path in files:
                    # Normalize timestamps and modes so touching files does not change hashes.
                    info = zipfile.ZipInfo(name + '/' + path.relative_to(base).as_posix(),
                                           date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, path.read_bytes(), compresslevel=9)
            with zipfile.ZipFile(target) as archive:
                bad = archive.testzip()
                if bad:
                    raise RuntimeError('Corrupt archive: ' + bad)
        write_checksums(stage)
        verify_checksums(stage)
        stage.rename(destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--checksums-only', metavar='DIRECTORY',
                      help='Write SHA256SUMS.txt for the ZIPs in this folder without repacking them')
    mode.add_argument('--verify', metavar='DIRECTORY',
                      help='Verify ZIP hashes and an exact match with SHA256SUMS.txt')
    parser.add_argument('--include-source', action='store_true',
                        help='Also build a whole-repository source ZIP (default: three plugins only)')
    args = parser.parse_args(argv)
    if args.include_source and (args.checksums_only or args.verify):
        parser.error('--include-source only applies when building archives')
    try:
        if args.checksums_only:
            directory = Path(args.checksums_only)
            write_checksums(directory)
        elif args.verify:
            directory = Path(args.verify)
        else:
            directory = build_release(ROOT, include_source=args.include_source)
            print('Archives contain source + installers, not preinstalled dependencies/models.')
        names = verify_checksums(directory)
        print('Verified {} ZIPs: {}'.format(len(names), directory.resolve()))
        print('Release attachments: ' + ', '.join(names + [MANIFEST]))
        return 0
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        print('[FAIL] ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
