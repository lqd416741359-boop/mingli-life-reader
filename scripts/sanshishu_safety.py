#!/usr/bin/env python3
"""三世书条目安全改写工具。

保留传统文化主题，但不输出寿命、死亡方式、疾病诊断、克亲断言或付费仪式。
"""

import re


def soften_traditional_entry(text):
    text = str(text or '')
    notes = []

    if re.search(r'(短寿|长寿|寿终|寿元|阎王|\d+岁|摔死|死日|棺木|送终|披麻|土葬|火葬)', text):
        text = re.sub(r'[^，。；]*(?:短寿|长寿|寿终|寿元|阎王|\d+岁|摔死|死日|棺木|送终|披麻|土葬|火葬)[^，。；]*[，。；]?', '', text)
        notes.append('本版不展示寿命或死亡方式预测。')

    if re.search(r'(疾病|肺炎|暗疾|瘟疾|病症|病痛)', text):
        text = re.sub(r'[^，。；]*(?:疾病|肺炎|暗疾|瘟疾|病症|病痛)[^，。；]*[，。；]?', '', text)
        notes.append('健康内容改为生活方式提醒，实际以体检和医生意见为准。')

    if re.search(r'(刑克|克亲|克父|克母|克儿|损及身|克妻|克夫)', text):
        text = re.sub(r'[^，。；]*(?:刑克|克亲|克父|克母|克儿|损及身|克妻|克夫)[^，。；]*[，。；]?', '', text)
        notes.append('亲缘内容改为沟通距离、责任分配与家庭边界的象征性观察。')

    if re.search(r'(烧化|纸钱|元宝|香烛|脱难钱|表文|法事|消灾钱)', text):
        text = re.sub(r'[^，。；]*(?:烧化|纸钱|元宝|香烛|脱难钱|表文|法事|消灾钱)[^，。；]*[，。；]?', '', text)
        notes.append('不建议购买物品或付费仪式；可用公益、修复关系和规律生活表达善意。')

    cleaned = re.sub(r'[，；]{2,}', '，', text).strip('，。； ')
    parts = ([cleaned + '。'] if cleaned else []) + notes
    return ''.join(parts)


def build_sanshishu_section(title, traditional, plain, advice):
    return {
        'title': title,
        'traditional': soften_traditional_entry(traditional),
        'plain': plain,
        'advice': advice,
        'notice': '传统民俗寓言，仅用于文化阅读和自我反思，不是事实预测。',
    }
