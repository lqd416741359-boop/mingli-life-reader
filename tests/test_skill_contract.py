import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from report_structure import validate_v2_reading  # noqa: E402


SKILL = ROOT / "SKILL.md"
README = ROOT / "README.md"
EXAMPLE = ROOT / "references" / "reading_v2_example.json"
COVER = ROOT / "assets" / "mingli-life-reader-v2-cover.png"


class SkillContractTest(unittest.TestCase):
    def test_example_uses_all_required_chapters(self):
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(validate_v2_reading(example), [])

    def test_skill_names_v2_fields_and_privacy_rule(self):
        text = SKILL.read_text(encoding="utf-8")
        for field in (
            "verdict",
            "manifestations",
            "strengths",
            "pitfalls",
            "actions",
            "evidence",
        ):
            self.assertIn(field, text)
        self.assertIn("真实命主", text)

    def test_readme_documents_v2_and_pdf_export(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("reading_v2_example.json", text)
        self.assertIn("打印", text)
        self.assertIn("PDF", text)
        self.assertIn("不要把真实", text)

    def test_readme_uses_repository_cover(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("assets/mingli-life-reader-v2-cover.png", text)
        self.assertTrue(COVER.is_file())
        self.assertGreater(COVER.stat().st_size, 100_000)


if __name__ == "__main__":
    unittest.main()
