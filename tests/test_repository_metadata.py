"""Keep current release metadata and documentation consistent; no network required."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ('DDDDOCR_Captcha_Umi', 'HyperLPR3_Plate_CPU', 'PPOCRv6_ONNX_CPU')


class RepositoryMetadataTests(unittest.TestCase):
    def test_current_versions_are_one_stable_version(self):
        version = (ROOT / 'VERSION.txt').read_text().strip()
        self.assertRegex(version, r'^\d+\.\d+\.\d+$')
        for name in PLUGINS:
            self.assertEqual((ROOT / 'plugins' / name / 'VERSION.txt').read_text().strip(), version)

    def test_standalone_plugin_guides_match_repository_guides(self):
        for filename in ('WINDOWS_ACCEPTANCE.md', 'OFFLINE_PRIVACY.md'):
            expected = (ROOT / 'docs' / filename).read_bytes()
            for name in PLUGINS:
                self.assertEqual((ROOT / 'plugins' / name / 'docs' / filename).read_bytes(), expected)

    def test_markdown_relative_file_links_exist(self):
        for document in ROOT.rglob('*.md'):
            if any(part in ('dist', '.git', 'site-packages', '_downloads') for part in document.parts):
                continue
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):
                    continue
                target = target.split('#', 1)[0]
                self.assertTrue((document.parent / target).exists(), '{}: {}'.format(document, target))

    def test_lock_metadata_is_current_without_changing_profiles(self):
        dependency = json.loads((ROOT / 'dependencies.lock.json').read_text())
        self.assertTrue(dependency['status'].startswith('stable;'))
        self.assertEqual(dependency['python'], '3.8')
        self.assertEqual(dependency['architecture'], 'win_amd64')
        for name in PLUGINS:
            root = ROOT / 'plugins' / name
            self.assertEqual(json.loads((root / 'dependencies.lock.json').read_text()), dependency)
            assets = json.loads((root / 'tools/assets.lock.json').read_text())
            self.assertIn('stable;', assets['profile'])
            self.assertIn('Win7 not supported', assets['profile'])

    def test_current_plugin_readmes_do_not_claim_pending_acceptance(self):
        version = (ROOT / 'VERSION.txt').read_text().strip()
        for name in PLUGINS:
            readme = (ROOT / 'plugins' / name / 'README.md').read_text(encoding='utf-8')
            self.assertIn('版本 ' + version + '，正式版', readme)
            self.assertNotIn('尚需实机', readme)
            self.assertNotIn('Win7 是最低目标系统', readme)


if __name__ == '__main__':
    unittest.main(verbosity=2)
