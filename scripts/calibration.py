# -*- coding: utf-8 -*-
"""命盘校准问题模块

用于收集用户实际情况，与命盘解读进行对比验证，提高解读准确度。
格式：question_id, question_text, hint, 对应命盘关键点, 验证逻辑
"""

# ============================================================
# 标准校准问题列表（按优先级排序）
# 使用说明：
# - 感情/婚姻、财运状况：必问
# - 事业/工作模式、生活变化/压力：选问
# - 根据用户实际情况选择 3-5 个最相关的追问
# ============================================================

CALIBRATION_QUESTIONS = [
    {
        'id': 'q1_marriage',
        'text': '你的感情/婚姻状态属于哪种？',
        'hint': '（可简单描述：稳定/波折/单身/其他）',
        'priority': 'high',
        'check_points': [
            '夫妻宫主星',
            '命宫星曜组合',
            '大限转换（2014→2019）',
            '流年桃花/感情'
        ],
        'response_examples': [
            '感情稳定，已婚多年',
            '有过婚姻变动/离婚',
            '单身，感情空白',
            '感情波折但目前稳定'
        ]
    },
    {
        'id': 'q2_marriage_detail',
        'text': '如果已婚/有伴侣，有没有重大感情事件？',
        'hint': '（如：结婚年份、2019年前后有无变动、生育等）',
        'priority': 'high',
        'check_points': [
            '2016-2019年感情变化',
            '命盘大限转换点',
            '夫妻宫四化'
        ],
        'response_examples': [
            '2016结婚生女，2019差点离婚，目前已稳定',
            '2018结婚，2020离婚，目前单身',
            '2015结婚至今感情稳定，有一孩',
            '2019感情重创，之后慢慢恢复'
        ]
    },
    {
        'id': 'q3_finance',
        'text': '最近1-2年财务状况如何？',
        'hint': '（如：收入变化、投资损益、负债、理财收益等）',
        'priority': 'high',
        'check_points': [
            '财帛宫星曜',
            '当前大限财务宫',
            '铃星/擎羊位置'
        ],
        'response_examples': [
            '最近一两年压力很大，收入锐减，投资亏损，外面还有欠款收不回来',
            '收入稳定但没什么增长，投资理财小赚',
            '事业上升期，财务状况明显改善',
            '有盈有亏，整体持平'
        ]
    },
    {
        'id': 'q4_career',
        'text': '你的事业/工作模式是怎样的？',
        'hint': '（如：打工/创业/自由职业/投资理财为主）',
        'priority': 'medium',
        'check_points': [
            '官禄宫主星',
            '命宫借宫星曜',
            '财帛宫组合'
        ],
        'response_examples': [
            '打工/上班',
            '创业/做生意',
            '自由职业/顾问',
            '投资理财为主',
            '混合模式'
        ]
    },
    {
        'id': 'q5_lifestyle',
        'text': '最近1-2年有没有明显的生活变化或压力来源？',
        'hint': '（如：换城市、生活节奏变化、经济压力、家庭成员变动等）',
        'priority': 'medium',
        'check_points': [
            '当前大限流年状态',
            '迁移宫/疾厄宫',
            '命盘整体格局'
        ],
        'response_examples': [
            '换城市工作，生活节奏变快',
            '家庭压力（父母/子女/配偶）',
            '经济压力为主',
            '整体平稳没什么大变化'
        ]
    },
    {
        'id': 'q6_health',
        'text': '有没有明显的身体不适或反复出现的健康问题？',
        'hint': '（如：睡眠、消化、慢性病等）',
        'priority': 'low',
        'check_points': [
            '疾厄宫主星',
            '流年健康宫位',
            '命盘整体健康象'
        ],
        'response_examples': [
            '睡眠不好，经常失眠',
            '肠胃问题',
            '没什么大问题',
            '有XX慢性病'
        ]
    },
    {
        'id': 'q7_parent_influence',
        'text': '父母中哪一方影响你更深？',
        'hint': '（性格、三观、职业等方面）',
        'priority': 'low',
        'check_points': [
            '父母宫主星',
            '田宅宫组合'
        ],
        'response_examples': [
            '母亲影响更深',
            '父亲影响更深',
            '双方都有影响',
            '单亲家庭/孤儿'
        ]
    }
]


def get_calibration_questions():
    """返回所有校准问题"""
    return CALIBRATION_QUESTIONS


def format_for_reading(questions):
    """格式化为LLM解读用的prompt"""
    formatted = []
    for i, q in enumerate(questions, 1):
        line = f"{i}. {q['text']}"
        if q.get('hint'):
            line += f" {q['hint']}"
        formatted.append(line)
    return '\n'.join(formatted)


def get_question_by_id(question_id):
    """根据ID获取单个问题"""
    for q in CALIBRATION_QUESTIONS:
        if q['id'] == question_id:
            return q
    return None


def validate_response(question_id, user_response, chart_context):
    """验证用户回答与命盘的一致性（基础版本）

    Args:
        question_id: 问题ID
        user_response: 用户回答文本
        chart_context: 命盘上下文（包含关键星曜/宫位信息）

    Returns:
        dict: {
            'match': True/False,  # 是否匹配
            'confidence_delta': +/-5~15,  # 置信度调整
            'analysis': '简要分析'
        }
    """
    q = get_question_by_id(question_id)
    if not q:
        return {'match': None, 'confidence_delta': 0, 'analysis': '未知问题'}

    # 基础实现：返回待验证状态
    return {
        'match': None,
        'confidence_delta': 0,
        'analysis': '请人工核对回答与命盘是否一致'
    }


# 用于生成HTML显示的简化格式
def get_questions_for_html():
    """返回适合HTML模板显示的问题列表"""
    return [
        {
            'text': q['text'],
            'hint': q.get('hint', '')
        }
        for q in CALIBRATION_QUESTIONS
    ]


if __name__ == '__main__':
    print("=== 校准问题列表 ===\n")
    print(format_for_reading(CALIBRATION_QUESTIONS))
    print("\n\n=== HTML格式 ===")
    for q in get_questions_for_html():
        print(q)
