import unittest
import importlib.util
import sys
import types
from pathlib import Path

# Provide dummy modules for external dependencies so snipe-IT.py can be imported
for name in ['requests', 'googleAuth', 'gemini']:
    sys.modules.setdefault(name, types.ModuleType(name))

# Dummy dotenv with load_dotenv function
dotenv_mod = types.ModuleType('dotenv')
setattr(dotenv_mod, 'load_dotenv', lambda *args, **kwargs: None)
sys.modules.setdefault('dotenv', dotenv_mod)

# Dummy tqdm with tqdm callable
tqdm_mod = types.ModuleType('tqdm')
setattr(tqdm_mod, 'tqdm', lambda *args, **kwargs: None)
setattr(tqdm_mod, 'write', lambda *args, **kwargs: None)
sys.modules.setdefault('tqdm', tqdm_mod)

MODULE_PATH = Path(__file__).resolve().parents[1] / 'snipe-IT.py'
spec = importlib.util.spec_from_file_location('snipe_it', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
format_mac = module.format_mac

class TestFormatMac(unittest.TestCase):
    def test_normalizes_plain_mac(self):
        self.assertEqual(format_mac('a81d166742f7'), 'a8:1d:16:67:42:f7')

    def test_already_formatted_returned(self):
        mac = 'a8:1d:16:67:42:f7'
        self.assertEqual(format_mac(mac), mac)

    def test_none_returned(self):
        self.assertIsNone(format_mac(None))

if __name__ == '__main__':
    unittest.main()
