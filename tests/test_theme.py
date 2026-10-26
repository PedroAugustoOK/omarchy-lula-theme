"""Regression coverage for malformed inputs and real installed-theme checks."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('theme_check', ROOT / 'scripts/check-theme.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class ThemeChecks(unittest.TestCase):
    def test_published_package_passes(self):
        self.assertEqual(CHECK.audit(ROOT)[0], [])

    def malformed_palette(self, text):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'colors.toml').write_text(text)
            return CHECK.audit(root)[0]

    def test_duplicate_toml_key_is_rejected(self):
        errors = self.malformed_palette('mode="dark"\nmode="light"\n')
        self.assertTrue(errors)
        self.assertIn('colors.toml', errors[0])

    def test_unknown_mode_is_rejected(self):
        text = (ROOT / 'colors.toml').read_text()
        text = text.replace('mode = "light"', 'mode = "invalid"').replace('mode = "dark"', 'mode = "invalid"')
        self.assertIn('mode must be light or dark', self.malformed_palette(text))

    def test_malformed_hex_is_reported_without_crashing(self):
        text = (ROOT / 'colors.toml').read_text()
        import re
        text = re.sub(r'foreground = "#[^"]+"', 'foreground = "#GG0000"', text, count=1)
        self.assertIn('foreground: expected a six-digit hex color', self.malformed_palette(text))

    def test_truncated_png_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'broken.png'
            path.write_bytes((ROOT / 'preview.png').read_bytes()[:33])
            with self.assertRaises(ValueError):
                CHECK.png_size(path)

    def test_checksum_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'broken.png'
            data = bytearray((ROOT / 'preview.png').read_bytes())
            data[29] ^= 1
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'checksum'):
                CHECK.png_size(path)


if __name__ == '__main__':
    unittest.main()
