import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from report_structure import (  # noqa: E402
    CHAPTER_ORDER,
    ReadingStructureError,
    normalize_reading,
    validate_v2_reading,
)
from generate_html import generate_html  # noqa: E402


TEMPLATE = ROOT / "templates" / "chart_template.html"
BRANCHES = "巳午未申酉戌亥子丑寅卯辰"
CHART = {
    "soul_palace_branch": "巳",
    "body_palace_branch": "午",
    "hour_index": 6,
    "gender": "女",
    "five_elements": "木三局",
    "solar_date": "",
    "lunar_date": "示例日期",
    "chinese_date": "甲子 示例",
    "year_mutagens": [],
    "palaces": [
        {
            "name": "命宫" if branch == "巳" else f"示例宫{index}",
            "earthly_branch": branch,
            "major_stars": ["示例星"] if branch == "巳" else [],
            "minor_stars": [],
            "mutagens": [],
            "tags": ["命宫"] if branch == "巳" else [],
        }
        for index, branch in enumerate(BRANCHES)
    ],
}


def make_complete_reading():
    chapters = {}
    for key in CHAPTER_ORDER:
        chapters[key] = {
            "title": key,
            "verdict": f"{key}核心判断",
            "manifestations": ["现实表现一", "现实表现二"],
            "strengths": ["可利用的优势"],
            "pitfalls": ["需要留意的习惯"],
            "actions": ["可以执行的第一步", "可以执行的第二步"],
            "evidence": {
                "ziwei": "紫微依据",
                "bazi": "八字依据",
                "relationship": "两套体系互相补充",
            },
        }
    return {
        "format_version": 2,
        "overview": {
            "title": "一分钟看懂",
            "items": ["核心优势", "主要课题", "当前阶段", "近期重点"],
        },
        "chapters": chapters,
        "calibration_questions": [],
    }


class ReportStructureContractTest(unittest.TestCase):
    def test_complete_v2_reading_has_no_errors(self):
        self.assertEqual(validate_v2_reading(make_complete_reading()), [])

    def test_missing_chapter_names_key_in_error(self):
        reading = make_complete_reading()
        del reading["chapters"]["wealth"]
        self.assertIn("wealth", "\n".join(validate_v2_reading(reading)))

    def test_blank_actions_field_is_rejected(self):
        reading = make_complete_reading()
        reading["chapters"]["career"]["actions"] = []
        self.assertIn("career.actions", "\n".join(validate_v2_reading(reading)))

    def test_legacy_cards_remain_legacy(self):
        reading = {"cards": [{"title": "旧版", "body": "内容"}]}
        self.assertEqual(normalize_reading(reading)["format"], "legacy")

    def test_v2_chapters_render_in_contract_order(self):
        output = generate_html(CHART, make_complete_reading(), TEMPLATE)
        positions = [output.index(f'data-chapter="{key}"') for key in CHAPTER_ORDER]
        self.assertEqual(positions, sorted(positions))

    def test_invalid_v2_reading_raises_readable_error(self):
        reading = make_complete_reading()
        del reading["chapters"]["relationship"]
        with self.assertRaisesRegex(ReadingStructureError, "relationship"):
            generate_html(CHART, reading, TEMPLATE)

    def test_legacy_cards_still_render(self):
        output = generate_html(
            CHART,
            {"cards": [{"title": "旧版标题", "body": "旧版内容"}]},
            TEMPLATE,
        )
        self.assertIn("旧版标题", output)
        self.assertIn("旧版内容", output)

    def test_v2_html_has_overview_and_expandable_evidence(self):
        output = generate_html(CHART, make_complete_reading(), TEMPLATE)
        self.assertIn('class="overview-panel"', output)
        self.assertIn('class="chapter-evidence"', output)

    def test_print_expands_professional_evidence(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("@media print", template)
        self.assertIn("details.chapter-evidence:not([open])", template)
        self.assertIn(".chapter-evidence>summary", template)
        self.assertIn("display:block!important", template)


if __name__ == "__main__":
    unittest.main()
