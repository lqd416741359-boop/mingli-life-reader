import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'bazi_calculator.py'
SPEC = importlib.util.spec_from_file_location('bazi_calculator', SCRIPT)
BAZI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BAZI
SPEC.loader.exec_module(BAZI)


class PaperThemeTest(unittest.TestCase):
    def test_print_keeps_pale_yellow_paper_background(self):
        template = (ROOT / 'templates' / 'chart_template.html').read_text(encoding='utf-8')
        self.assertIn('print-color-adjust:exact', template)
        self.assertNotIn('@media print{body{background:#fff}', template)


class BoneReadingTest(unittest.TestCase):
    def test_31_qian_explains_its_own_poem(self):
        title, explanation = BAZI._bone_plain_reading(31)
        self.assertIn('三两一钱', title)
        self.assertIn('忙忙碌碌', explanation)
        self.assertIn('中年', explanation)
        self.assertIn('建立自己的基础', explanation)

    def test_39_qian_has_specific_plain_language_interpretation(self):
        title, explanation = BAZI._bone_plain_reading(39)
        self.assertIn('三两九钱', title)
        self.assertIn('早期', explanation)
        self.assertIn('一次受挫', explanation)
        self.assertIn('调整方法', explanation)
        self.assertNotIn('高度概括的旧式语言', explanation)


if __name__ == '__main__':
    unittest.main()
