"""Regression tests for release bundles and checksum manifests; no network needed."""
import contextlib
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('make_release', str(ROOT / 'scripts/make_release.py'))
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'VERSION.txt').write_text('1.2.3\n')
        (self.root / 'README.md').write_text('Source archive documentation\n')
        for name in release.PLUGINS:
            plugin = self.root / 'plugins' / name
            plugin.mkdir(parents=True)
            (plugin / 'VERSION.txt').write_text('1.2.3\n')
            (plugin / '__init__.py').write_bytes(b'value = 1\r\n')

    def make_zip_folder(self):
        folder = self.root / 'downloaded'
        folder.mkdir()
        for name in ('a.zip', 'b.zip'):
            with zipfile.ZipFile(folder / name, 'w') as archive:
                archive.writestr('plugin/file.txt', name)
        return folder

    def test_default_bundle_has_exactly_three_plugins_and_manifest(self):
        folder = release.build_release(self.root)
        names = release.verify_checksums(folder)
        self.assertEqual(set(names), {name + '-v1.2.3.zip' for name in release.PLUGINS})
        self.assertEqual(len(list(folder.iterdir())), 4)
        for path in folder.glob('*.zip'):
            plugin = path.name[:-len('-v1.2.3.zip')]
            with zipfile.ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(archive.read(plugin + '/__init__.py'), b'value = 1\r\n')
                self.assertEqual(archive.namelist(), [plugin + '/VERSION.txt', plugin + '/__init__.py'])

    def test_rebuild_is_isolated_and_does_not_mix_stale_files(self):
        first = release.build_release(self.root)
        stale = first / 'deleted-plugin-v0.1.zip'
        stale.write_bytes(b'old release')
        loose = self.root / 'dist/old.zip'
        loose.write_bytes(b'old loose ZIP')
        second = release.build_release(self.root)
        self.assertNotEqual(first, second)
        self.assertEqual(len(release.verify_checksums(second)), 3)
        self.assertEqual(stale.read_bytes(), b'old release')
        self.assertEqual(loose.read_bytes(), b'old loose ZIP')

    def test_same_bytes_same_hash_after_touching_files(self):
        first = release.build_release(self.root)
        for path in (self.root / 'plugins').rglob('*'):
            if path.is_file():
                os.utime(str(path), (1800000000, 1800000000))
        second = release.build_release(self.root)
        self.assertEqual((first / release.MANIFEST).read_bytes(), (second / release.MANIFEST).read_bytes())

    def test_optional_source_is_listed_but_never_includes_dist(self):
        old = self.root / 'dist/old'
        old.mkdir(parents=True)
        (old / 'leak.txt').write_text('must not be packaged')
        folder = release.build_release(self.root, include_source=True)
        self.assertEqual(len(release.verify_checksums(folder)), 4)
        source = folder / 'umi-ocr-swiss-army-knife-source-v1.2.3.zip'
        with zipfile.ZipFile(source) as archive:
            self.assertTrue(any(name.endswith('/README.md') for name in archive.namelist()))
            self.assertFalse(any('/dist/' in name for name in archive.namelist()))

    def test_runtime_data_and_reports_are_excluded(self):
        plugin = self.root / 'plugins' / release.PLUGINS[0]
        for directory in ('models', 'site-packages', '_downloads', '__pycache__', '_deps_stage_old'):
            (plugin / directory).mkdir()
            (plugin / directory / 'private.txt').write_text('must not be packaged')
        for filename in ('environment-report.json', 'audit-local-results.json', 'sample.png', 'debug.log'):
            (plugin / filename).write_text('must not be packaged')
        folder = release.build_release(self.root)
        with zipfile.ZipFile(folder / (plugin.name + '-v1.2.3.zip')) as archive:
            self.assertEqual(len(archive.namelist()), 2)

    def test_required_plugin_and_version_mismatch_fail_before_output(self):
        version = self.root / 'plugins' / release.PLUGINS[0] / 'VERSION.txt'
        version.write_text('1.2.2')
        with self.assertRaisesRegex(ValueError, 'Version mismatch'):
            release.build_release(self.root)
        self.assertFalse((self.root / 'dist').exists())
        version.write_text('1.2.3')
        version.parent.rename(version.parent.with_name('renamed'))
        with self.assertRaisesRegex(ValueError, 'Missing plugin'):
            release.build_release(self.root)

    def test_invalid_version_is_rejected(self):
        for version in ('', '..', '../outside', 'a\nb', 'v1.2.3'):
            (self.root / 'VERSION.txt').write_text(version)
            with self.assertRaisesRegex(ValueError, 'Invalid version'):
                release.build_release(self.root)

    def test_failed_build_cleans_only_its_temporary_directory(self):
        previous = release.build_release(self.root)
        before = (previous / release.MANIFEST).read_bytes()
        with mock.patch.object(release, 'write_checksums', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                release.build_release(self.root)
        self.assertEqual(list((self.root / 'dist').iterdir()), [previous])
        self.assertEqual((previous / release.MANIFEST).read_bytes(), before)

    def test_checksums_only_hashes_downloaded_bytes_without_repacking(self):
        folder = self.make_zip_folder()
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        release.write_checksums(folder)
        self.assertEqual(release.verify_checksums(folder), ['a.zip', 'b.zip'])
        for name, data in before.items():
            self.assertEqual((folder / name).read_bytes(), data)
            self.assertIn(hashlib.sha256(data).hexdigest(), (folder / release.MANIFEST).read_text())
        (folder / 'b.zip').unlink()
        release.write_checksums(folder)
        self.assertEqual(release.verify_checksums(folder), ['a.zip'])
        self.assertNotIn('b.zip', (folder / release.MANIFEST).read_text())

    def test_empty_directory_is_rejected(self):
        folder = self.root / 'empty'
        folder.mkdir()
        with self.assertRaisesRegex(ValueError, 'No ZIP files'):
            release.write_checksums(folder)
        self.assertFalse((folder / release.MANIFEST).exists())

    def test_missing_extra_and_modified_zip_are_rejected(self):
        folder = self.make_zip_folder()
        release.write_checksums(folder)
        original = (folder / 'a.zip').read_bytes()
        (folder / 'a.zip').unlink()
        with self.assertRaisesRegex(ValueError, 'missing:.*a.zip'):
            release.verify_checksums(folder)
        (folder / 'a.zip').write_bytes(original)
        (folder / 'extra.zip').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'not listed:.*extra.zip'):
            release.verify_checksums(folder)
        (folder / 'extra.zip').unlink()
        (folder / 'a.zip').write_bytes(b'modified')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch: a.zip'):
            release.verify_checksums(folder)

    def test_malformed_unsafe_and_duplicate_manifest_entries_are_rejected(self):
        folder = self.make_zip_folder()
        release.write_checksums(folder)
        manifest = folder / release.MANIFEST
        original = manifest.read_text()
        invalid = ['not a checksum\n', '0' * 64 + '  ../outside.zip\n',
                   '0' * 64 + '  C:\\outside.zip\n', original + original.splitlines()[0] + '\n',
                   original + original.splitlines()[0].replace('a.zip', 'A.zip') + '\n', '']
        for text in invalid:
            manifest.write_text(text)
            with self.assertRaises(ValueError):
                release.verify_checksums(folder)

    def test_checksum_symlink_is_rejected_and_target_untouched(self):
        folder = self.make_zip_folder()
        outside = self.root / 'outside.txt'
        outside.write_text('do not overwrite')
        try:
            (folder / release.MANIFEST).symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable on this host')
        for function in (release.write_checksums, release.verify_checksums):
            with self.assertRaisesRegex(ValueError, 'Symlink not allowed'):
                function(folder)
        self.assertEqual(outside.read_text(), 'do not overwrite')

    def test_failed_manifest_write_preserves_previous_manifest(self):
        folder = self.make_zip_folder()
        manifest = release.write_checksums(folder)
        before = manifest.read_bytes()
        with mock.patch.object(release.os, 'replace', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                release.write_checksums(folder)
        self.assertEqual(manifest.read_bytes(), before)
        self.assertFalse(list(folder.glob('.SHA256SUMS-*')))

    def test_cancelled_build_cleans_temporary_directory(self):
        previous = release.build_release(self.root)
        with mock.patch.object(release, 'write_checksums', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                release.build_release(self.root)
        self.assertEqual(list((self.root / 'dist').iterdir()), [previous])

    def test_excluded_directories_are_not_traversed(self):
        for name in ('dist', 'models', 'site-packages'):
            (self.root / name).mkdir()
            (self.root / name / 'private.txt').write_text('excluded')
        original = release.os.scandir

        def guarded(path):
            if Path(path).name in release.SKIP:
                self.fail('Traversed excluded directory: ' + str(path))
            return original(path)

        with mock.patch.object(release.os, 'scandir', side_effect=guarded):
            files = list(release.source_files(self.root))
        self.assertFalse(any(p.name == 'private.txt' for p in files))

    def test_line_separator_filename_is_rejected_before_manifest_write(self):
        folder = self.make_zip_folder()
        for separator in ('\x0b', '\u2028'):
            path = folder / ('odd' + separator + 'name.zip')
            try:
                path.write_bytes(b'zip')
            except OSError:
                continue  # Some filesystems already reject these names.
            try:
                with self.assertRaisesRegex(ValueError, 'Unsafe ZIP filename'):
                    release.write_checksums(folder)
                self.assertFalse((folder / release.MANIFEST).exists())
            finally:
                path.unlink()

    def test_cli_success_and_failure_exit_status(self):
        folder = self.make_zip_folder()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(release.main(['--checksums-only', str(folder)]), 0)
            self.assertEqual(release.main(['--verify', str(folder)]), 0)
            (folder / 'a.zip').write_bytes(b'corrupt')
            self.assertEqual(release.main(['--verify', str(folder)]), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
