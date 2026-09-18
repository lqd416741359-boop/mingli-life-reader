import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from sanshishu_safety import build_sanshishu_section, soften_traditional_entry
from generate_html import build_sanshishu_html


class SanshishuSafetyTest(unittest.TestCase):
    def test_softens_lifespan_and_death_predictions(self):
        result = soften_traditional_entry('短寿35岁，长寿59岁，从高处摔死，有一子送终。')
        self.assertNotIn('35岁', result)
        self.assertNotIn('59岁', result)
        self.assertNotIn('摔死', result)
        self.assertNotIn('送终', result)
        self.assertIn('不展示寿命或死亡方式预测', result)

    def test_softens_disease_and_family_harm_claims(self):
        result = soften_traditional_entry('中年注意脾胃疾病，父母刑克重，妻儿损及身。')
        self.assertNotIn('脾胃疾病', result)
        self.assertNotIn('刑克', result)
        self.assertNotIn('损及身', result)
        self.assertIn('生活方式', result)
        self.assertIn('家庭边界', result)

    def test_rejects_paid_ritual_prescriptions(self):
        result = soften_traditional_entry('用五土钱百二、元宝香烛，每日烧化脱难钱三十张。')
        self.assertNotIn('烧化', result)
        self.assertNotIn('三十张', result)
        self.assertIn('不建议购买物品或付费仪式', result)

    def test_builds_three_layer_entry(self):
        section = build_sanshishu_section(
            '论夫妻相',
            '针尖对麦芒，最终分离。',
            '关系中容易针锋相对，需要有人先暂停升级冲突。',
            '设置冷静时间，并约定一次只讨论一个问题。',
        )
        self.assertEqual(section['title'], '论夫妻相')
        self.assertEqual(set(section), {'title', 'traditional', 'plain', 'advice', 'notice'})
        self.assertIn('传统民俗', section['notice'])

    def test_renders_structured_section_for_report(self):
        output = build_sanshishu_html([{
            'title': '论夫妻相',
            'traditional': '针尖对麦芒。',
            'plain': '关系中容易针锋相对。',
            'advice': '先暂停，再讨论。',
            'notice': '传统民俗寓言。',
        }])
        self.assertIn('三世书 · 民俗条目白话解读', output)
        self.assertIn('传统意象', output)
        self.assertIn('白话解释', output)
        self.assertIn('现实建议', output)


if __name__ == '__main__':
    unittest.main()
