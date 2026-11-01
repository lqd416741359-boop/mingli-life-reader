#!/usr/bin/env python3
"""四柱八字扩展计算。

使用 lunar-python 提供确定性的历法、四柱、大运、流年和小运数据。
神煞采用 references/bazi_methodology.md 中列明的常用规则子集；称骨采用
民间通行查表法，仅作传统文化娱乐展示。
"""

from collections import Counter


GAN_ELEMENT = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
}
ZHI_ELEMENT = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
    '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水',
}
HOUR_VALUE = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8, 5: 10, 6: 12,
              7: 14, 8: 16, 9: 18, 10: 20, 11: 22, 12: 23}

ELEMENT_LIFESTYLE = {
    '木': {
        'directions': ['东方', '东南'], 'colors': ['青绿', '松石绿', '木色'],
        'careers': ['教育培训', '内容出版', '设计策划', '园林与环保', '成长型服务'],
        'leisure': ['徒步', '园艺', '阅读', '手作', '自然观察'],
    },
    '火': {
        'directions': ['南方'], 'colors': ['暖红', '珊瑚橙', '紫色'],
        'careers': ['传播媒体', '品牌营销', '视觉创意', '餐饮能源', '公众表达'],
        'leisure': ['舞蹈', '摄影', '观演', '烹饪', '有氧运动'],
    },
    '土': {
        'directions': ['本地与中心区域', '西南', '东北'], 'colors': ['米黄', '驼色', '陶土色'],
        'careers': ['项目管理', '地产空间', '供应链', '行政运营', '长期服务业'],
        'leisure': ['陶艺', '收纳', '露营', '烘焙', '慢旅行'],
    },
    '金': {
        'directions': ['西方', '西北'], 'colors': ['白色', '银灰', '香槟金'],
        'careers': ['金融审计', '法律合规', '工程制造', '数据分析', '品质管理'],
        'leisure': ['器械训练', '乐器', '收藏', '拼装', '极简整理'],
    },
    '水': {
        'directions': ['北方'], 'colors': ['深蓝', '灰蓝', '黑色'],
        'careers': ['咨询研究', '贸易物流', '旅游流动', '信息技术', '沟通服务'],
        'leisure': ['游泳', '旅行', '写作', '冥想', '水边散步'],
    },
}

ZODIAC = dict(zip('子丑寅卯辰巳午未申酉戌亥', '鼠牛虎兔龙蛇马羊猴鸡狗猪'))

TEN_GOD_PLAIN = {
    '比肩': ('自主并重型', '重视独立、平等和亲自掌控，适合靠专业与同辈协作；压力下容易固执或不愿求助。'),
    '劫财': ('竞争行动型', '行动快、敢争取、朋友缘与号召力较强；需要管好冲动、人情开支和合伙边界。'),
    '食神': ('温和创造型', '重体验、表达与长期作品，通常亲和、会照顾感受；要避免舒适过度或行动节奏偏慢。'),
    '伤官': ('创新表达型', '观察敏锐、敢质疑、表达和改进欲强；要学习把锋芒转成方案，减少与规则或权威的硬碰硬。'),
    '偏财': ('机会整合型', '对市场、人脉和资源流动较敏感，适合多场景连接；要避免追热点、分心与边界模糊。'),
    '正财': ('务实经营型', '看重可持续回报、责任和秩序，擅长把资源做实；要避免只顾安全而错失成长。'),
    '七杀': ('压力突破型', '目标感、执行力和危机反应较强，适合有挑战的任务；需要避免长期紧绷与过度强硬。'),
    '正官': ('规则责任型', '重信誉、标准与角色责任，适合制度清楚的环境；要避免过度在意评价或自我约束。'),
    '偏印': ('独特研究型', '擅长非标准学习、洞察和独立研究；压力下容易想得多、节奏跳跃或与人疏离。'),
    '正印': ('学习支持型', '吸收、归纳、照顾与知识传承能力较强；要防止准备过久、依赖熟悉路径而延迟行动。'),
}


def _ten_god_summary(pillars):
    """统计显性天干与藏干十神，并给出月令主气命格的温和说明。"""
    values = []
    for pillar in pillars:
        if pillar['name'] != '日柱' and pillar.get('ten_god_gan'):
            values.append(pillar['ten_god_gan'])
        values.extend(pillar.get('ten_god_zhi', []))
    counts = Counter(values)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    dominant = ranked[:3]
    month_main = next((p.get('ten_god_zhi', [''])[0] for p in pillars if p['name'] == '月柱'), '')
    if month_main == '比肩':
        pattern_name = '建禄取向（参考）'
    elif month_main == '劫财':
        pattern_name = '月刃取向（参考）'
    else:
        pattern_name = f'{month_main}格（参考）' if month_main else '综合取向'
    label, explanation = TEN_GOD_PLAIN.get(month_main, ('综合配置型', '需要结合月令、透干、根气与全局制化综合判断。'))
    profiles = [
        {'name': name, 'count': count, 'label': TEN_GOD_PLAIN.get(name, ('', ''))[0],
         'plain': TEN_GOD_PLAIN.get(name, ('', ''))[1]}
        for name, count in dominant
    ]
    return {
        'pattern_name': pattern_name,
        'pattern_basis': f'以月支主气“{month_main or "未识别"}”作入门标签',
        'plain_label': label,
        'plain_explanation': explanation,
        'counts': dict(counts),
        'dominant_profiles': profiles,
        'disclaimer': '这是便于普通人阅读的月令入门标签，不等于完成旺衰、调候、透干与制化后的专业定格。',
    }


YEAR_WEIGHTS = {
    '甲子': 12, '乙丑': 9, '丙寅': 6, '丁卯': 7, '戊辰': 12, '己巳': 5,
    '庚午': 9, '辛未': 8, '壬申': 7, '癸酉': 8, '甲戌': 15, '乙亥': 9,
    '丙子': 16, '丁丑': 8, '戊寅': 8, '己卯': 19, '庚辰': 12, '辛巳': 6,
    '壬午': 8, '癸未': 7, '甲申': 5, '乙酉': 15, '丙戌': 6, '丁亥': 16,
    '戊子': 15, '己丑': 7, '庚寅': 9, '辛卯': 12, '壬辰': 10, '癸巳': 7,
    '甲午': 15, '乙未': 6, '丙申': 5, '丁酉': 14, '戊戌': 14, '己亥': 9,
    '庚子': 7, '辛丑': 7, '壬寅': 9, '癸卯': 12, '甲辰': 8, '乙巳': 7,
    '丙午': 13, '丁未': 5, '戊申': 14, '己酉': 5, '庚戌': 9, '辛亥': 17,
    '壬子': 5, '癸丑': 7, '甲寅': 12, '乙卯': 8, '丙辰': 8, '丁巳': 6,
    '戊午': 19, '己未': 6, '庚申': 8, '辛酉': 16, '壬戌': 10, '癸亥': 6,
}
MONTH_WEIGHTS = [6, 7, 18, 9, 5, 16, 9, 15, 18, 8, 9, 5]
DAY_WEIGHTS = [5, 10, 8, 15, 16, 15, 8, 16, 8, 16, 9, 17, 8, 17, 10,
               8, 9, 18, 5, 15, 10, 9, 8, 9, 15, 18, 7, 8, 16, 6]
HOUR_WEIGHTS = {'子': 16, '丑': 6, '寅': 7, '卯': 10, '辰': 9, '巳': 16,
                '午': 10, '未': 8, '申': 8, '酉': 9, '戌': 6, '亥': 6}

BONE_POEMS = {
    21: '短命非业谓大空，平生灾难事重重，凶祸频临陷逆境，终世困苦事不成。',
    22: '身寒骨冷苦伶仃，此命推来行乞人，劳劳碌碌无度日，终年打拱过平生。',
    23: '此命推来骨格轻，求谋作事事难成，妻儿兄弟应难许，别处他乡作散人。',
    24: '此命推来福禄无，门庭困苦总难荣，六亲骨肉皆无靠，流浪他乡作老翁。',
    25: '此命推来祖业微，门庭营度似稀奇，六亲骨肉如冰炭，一世勤劳自把持。',
    26: '平生衣禄苦中求，独自营谋事不休，离祖出门宜早计，晚来衣禄自无忧。',
    27: '一生作事少商量，难靠祖宗作主张，独马单枪空做去，早年晚岁总无长。',
    28: '一生行事似飘蓬，祖宗产业在梦中，若不过房改名姓，也当移徙二三通。',
    29: '初年运限未曾亨，纵有功名在后成，须过四旬方可立，移居改姓始为良。',
    30: '劳劳碌碌苦中求，东奔西走何日休，若使终身勤与俭，老来稍可免忧愁。',
    31: '忙忙碌碌苦中求，何日云开见日头，难得祖基家可立，中年衣食渐无忧。',
    32: '初年运蹇事难谋，渐有财源如水流，到得中年衣食旺，那时名利一齐收。',
    33: '早年做事事难成，百计徒劳枉费心，半世自如流水去，后来运到得黄金。',
    34: '此命福气果如何，僧道门中衣禄多，离祖出家方为妙，朝晚拜佛念弥陀。',
    35: '生平福量不周全，祖业根基觉少传，营事生涯宜守旧，时来衣食胜从前。',
    36: '不须劳碌过平生，独自成家福不轻，早有福星常照命，任君行去百般成。',
    37: '此命般般事不成，弟兄少力自孤成，虽然祖业须微有，来得明时去不明。',
    38: '一身骨肉最清高，早入簧门姓氏标，待到年将三十六，蓝衣脱去换红袍。',
    39: '此命终身运不通，劳劳做事尽皆空，苦心竭力成家计，到得那时在梦中。',
    40: '平生衣禄是绵长，件件心中自主张，前面风霜多受过，后来必定享安康。',
    41: '此命推来自不同，为人能干异凡庸，中年还有逍遥福，不比前时运未通。',
    42: '得宽怀处且宽怀，何用双眉总不开，若使中年命运济，那时名利一齐来。',
    43: '为人心性最聪明，做事轩昂近贵人，衣禄一生天数定，不须劳碌过平生。',
    44: '万事由天莫苦求，须知福禄赖人修，当年财帛难如意，晚景欣然便不忧。',
    45: '名利推来竟若何，前番辛苦后奔波，命中难养男和女，骨肉扶持也不多。',
    46: '东西南北尽皆通，出姓移居更觉隆，衣禄无亏天数定，中年晚景一般同。',
    47: '此命推来旺末年，妻荣子贵自怡然，平生原有滔滔福，可卜财源若水泉。',
    48: '初年运道未曾亨，若是蹉跎再不兴，兄弟六亲皆无靠，一身事业晚来整。',
    49: '此命推来福不轻，自成自立显门庭，从来富贵人亲近，使婢差奴过一生。',
    50: '为利为名终日劳，中年福禄也多遭，老来是有财星照，不比前番目下高。',
    51: '一世荣华事事通，不须劳碌自亨通，弟兄叔侄皆如意，家业成时福禄宏。',
    52: '一世亨通事事能，不须劳思自然宁，宗族欣然心皆好，家业丰亨自称心。',
    53: '此格推来气象真，兴家发达在其中，一生福禄安排定，却是人间一富翁。',
    54: '此命推来厚且清，诗书满腹看功成，丰衣足食自然稳，正是人间有福人。',
    55: '走马扬鞭争利名，少年做事费功成，一朝福禄源源至，富贵荣华显六亲。',
    56: '此格推来礼义通，一生福禄用无穷，甜酸苦辣皆尝过，财源滚滚稳且丰。',
    57: '福禄盈盈万事全，一生荣耀显双亲，名扬威震人钦敬，处世逢凶化为吉。',
    58: '平生福禄自然来，名利兼全福寿偕，雁塔题名为贵客，紫袍金带走金阶。',
    59: '细推此格妙且清，必定才高礼义通，甲第之中应有分，扬鞭走马显威荣。',
    60: '一朝金榜快题名，显祖荣宗立大功，衣食定然原裕足，田园财帛更丰盈。',
    61: '不做朝中金榜客，定为世上大财翁，聪明天赋经书熟，名显高科自是荣。',
    62: '此命生来福不穷，读书必定显亲宗，紫衣金带为卿相，富贵荣华皆可同。',
    63: '命主为官福禄长，得来富贵定非常，名题金塔传金榜，定中高科天下扬。',
    64: '此格权威不可当，紫袍金带坐高堂，荣华富贵谁能及，积玉堆金满储仓。',
    65: '细推此命福非轻，富贵荣华孰与争，定国安邦人极品，威声显赫震寰瀛。',
    66: '此格人间一福人，堆金积玉满堂春，从来富贵由天定，正笏垂绅谒圣君。',
    67: '此命生来福自宏，田园家业最高隆，平生衣禄盈丰足，一世荣华万事通。',
    68: '富贵由天莫苦求，万金家计不须谋，十年不比前番事，一旦遂心百事谋。',
    69: '君是人间衣禄星，一生富贵众人钦，纵然福禄由天定，安享荣华过一生。',
    70: '此命推来福禄宏，不须劳碌自亨通，田园产业家昌盛，大富大贵不受穷。',
    71: '此命生成大不同，公侯卿相在其中，一生自有逍遥福，富贵荣华极品隆。',
    72: '此格世界罕有生，十代积善产此人，天上紫微来照命，统治万民乐太平。',
}


def _group_value(zhi, mapping):
    for group, value in mapping.items():
        if zhi in group:
            return value
    return None


def common_shensha(day_gan, day_zhi, year_zhi, target_zhi):
    """返回一组常见神煞；规则来源与边界见 bazi_methodology.md。"""
    stars = []
    tianyi = {
        '甲': '丑未', '戊': '丑未', '庚': '丑未', '乙': '子申', '己': '子申',
        '丙': '亥酉', '丁': '亥酉', '壬': '卯巳', '癸': '卯巳', '辛': '午寅',
    }
    single_by_gan = {
        '文昌贵人': {'甲': '巳', '乙': '午', '丙': '申', '丁': '酉', '戊': '申',
                 '己': '酉', '庚': '亥', '辛': '子', '壬': '寅', '癸': '卯'},
        '禄神': {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
               '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'},
        '羊刃': {'甲': '卯', '乙': '寅', '丙': '午', '丁': '巳', '戊': '午',
               '己': '巳', '庚': '酉', '辛': '申', '壬': '子', '癸': '亥'},
    }
    if target_zhi in tianyi.get(day_gan, ''):
        stars.append('天乙贵人')
    for name, table in single_by_gan.items():
        if table.get(day_gan) == target_zhi:
            stars.append(name)

    group_rules = {
        '桃花': {'申子辰': '酉', '寅午戌': '卯', '亥卯未': '子', '巳酉丑': '午'},
        '驿马': {'申子辰': '寅', '寅午戌': '申', '亥卯未': '巳', '巳酉丑': '亥'},
        '华盖': {'申子辰': '辰', '寅午戌': '戌', '亥卯未': '未', '巳酉丑': '丑'},
        '将星': {'申子辰': '子', '寅午戌': '午', '亥卯未': '卯', '巳酉丑': '酉'},
        '劫煞': {'申子辰': '巳', '寅午戌': '亥', '亥卯未': '申', '巳酉丑': '寅'},
    }
    for name, mapping in group_rules.items():
        if target_zhi in {_group_value(day_zhi, mapping), _group_value(year_zhi, mapping)}:
            stars.append(name)

    hongluan = dict(zip('子丑寅卯辰巳午未申酉戌亥', '卯寅丑子亥戌酉申未午巳辰'))
    tianxi = dict(zip('子丑寅卯辰巳午未申酉戌亥', '酉申未午巳辰卯寅丑子亥戌'))
    if hongluan.get(year_zhi) == target_zhi:
        stars.append('红鸾')
    if tianxi.get(year_zhi) == target_zhi:
        stars.append('天喜')
    return list(dict.fromkeys(stars))


def _pillar(name, ec, prefix, day_gan, day_zhi, year_zhi):
    ganzhi = getattr(ec, f'get{prefix}')()
    gan = getattr(ec, f'get{prefix}Gan')()
    zhi = getattr(ec, f'get{prefix}Zhi')()
    return {
        'name': name, 'ganzhi': ganzhi, 'gan': gan, 'zhi': zhi,
        'gan_element': GAN_ELEMENT[gan], 'zhi_element': ZHI_ELEMENT[zhi],
        'hidden_stems': list(getattr(ec, f'get{prefix}HideGan')()),
        'ten_god_gan': getattr(ec, f'get{prefix}ShiShenGan')(),
        'ten_god_zhi': list(getattr(ec, f'get{prefix}ShiShenZhi')()),
        'nayin': getattr(ec, f'get{prefix}NaYin')(),
        'dishi': getattr(ec, f'get{prefix}DiShi')(),
        'xunkong': getattr(ec, f'get{prefix}XunKong')(),
        'shen_sha': common_shensha(day_gan, day_zhi, year_zhi, zhi),
    }


def _bone_plain_reading(total):
    """返回与具体重量对应的现代解读；未专门收录时使用安全回退。"""
    readings = {
        31: (
            '三两一钱白话解读：先建立自己的基础，后面的路会更稳',
            '“忙忙碌碌苦中求”可理解为早期常需要亲自摸索，付出的时间和精力比较多；'
            '“何日云开见日头”表达的是对转机的期待，现实中不宜只等待机会，而要持续累积技能、信用和可靠关系；'
            '“难得祖基家可立”不必解释成没有家庭帮助，更适合提醒不要把长期计划完全建立在现成资源上，要逐步建立自己的基础；'
            '“中年衣食渐无忧”描述的是经验和能力经过时间沉淀后，生活稳定度可能提高。'
            '现实建议是减少无方向的忙忙碌碌，把力气集中在能够复利的专业、现金流和长期合作上。'
        ),
        39: (
            '三两九钱白话解读：费力感不等于没有出路',
            '“终身运不通”是旧式歌诀的夸张说法，更适合解释为早期推进事情时，容易觉得阻力较多、回报来得较慢；'
            '“劳劳做事尽皆空”提醒的是只靠反复用力，未必能得到相称结果，需要检查方向、合作方式和资源配置；'
            '“苦心竭力成家计”反映出较强的责任感，容易把家庭、工作或经济压力都揽在自己身上；'
            '“到得那时在梦中”不是说努力必然落空，而是提醒不要把希望只放在遥远结果上。'
            '现实中应避免把一次受挫理解成一生不顺，更有效的做法是及时调整方法、积累可复用的能力、保留现金与精力余量，并让目标分阶段落地。'
        ),
        43: (
            '四两三钱白话解读：聪明不是省力，而是懂得用对力',
            '“为人心性最聪明”可理解为领悟较快、会观察局势，也较懂得把复杂事情理出头绪；'
            '“做事轩昂近贵人”不是保证遇到权贵，而是说在专业、正式或有规则的场合，较容易凭表达、判断和办事能力获得前辈或负责人认可；'
            '“不须劳碌”也不是可以躺平，而是提醒少做低效蛮干，多靠专业技能、流程、沟通和可靠关系放大成果。'
            '现实中的提醒是：反应快的人也可能想得太多、在意体面，真正有用的是把聪明落实成可重复的能力与持续行动。'
        ),
    }
    return readings.get(total, (
        f'{total // 10}两{total % 10}钱白话解读：把古歌转成生活提醒',
        '这段歌诀使用高度概括的旧式语言，应先理解它描述的是处事方式与人生节奏，而不是对学历、财富、婚姻或寿命的判决。'
        '阅读时可分别找出歌中关于行动、关系、责任和节奏的提示，再与四柱结构、现实经历和个人选择互相核对；'
        '有消极字句时，不逐字套用，也不把阶段性困难扩大成终身结论。'
    ))


def _bone_weight(lunar, ec):
    lunar_month = abs(lunar.getMonth())
    lunar_day = lunar.getDay()
    year_gz = ec.getYear()
    hour_zhi = ec.getTimeZhi()
    parts = {
        'year': YEAR_WEIGHTS[year_gz],
        'month': MONTH_WEIGHTS[lunar_month - 1],
        'day': DAY_WEIGHTS[lunar_day - 1],
        'hour': HOUR_WEIGHTS[hour_zhi],
    }
    total = sum(parts.values())
    plain_title, plain_explanation = _bone_plain_reading(total)
    return {
        'version': '民间通行查表版（不分男女，闰月按同月）',
        'total_qian': total,
        'display': f'{total // 10}两{total % 10}钱',
        'breakdown_qian': parts,
        'poem': BONE_POEMS.get(total, '该重量在不同传本中存在差异，暂不强行匹配歌诀。'),
        'plain_title': plain_title,
        'plain_explanation': plain_explanation,
        'disclaimer': '称骨是独立的民俗查表法，不代表八字强弱，也不宜据此做现实决策。',
    }


def calculate_bazi(date_str, hour_index, gender, is_lunar=False, is_leap=False,
                   target_year=None, dayun_count=8):
    from lunar_python import Lunar, Solar

    year, month, day = [int(x) for x in date_str.split('-')]
    hour = HOUR_VALUE[hour_index]
    if is_lunar:
        lunar_month = -month if is_leap else month
        lunar = Lunar.fromYmdHms(year, lunar_month, day, hour, 0, 0)
    else:
        lunar = Solar.fromYmdHms(year, month, day, hour, 0, 0).getLunar()

    ec = lunar.getEightChar()
    day_gan, day_zhi, year_zhi = ec.getDayGan(), ec.getDayZhi(), ec.getYearZhi()
    pillars = [
        _pillar('年柱', ec, 'Year', day_gan, day_zhi, year_zhi),
        _pillar('月柱', ec, 'Month', day_gan, day_zhi, year_zhi),
        _pillar('日柱', ec, 'Day', day_gan, day_zhi, year_zhi),
        _pillar('时柱', ec, 'Time', day_gan, day_zhi, year_zhi),
    ]

    counts = Counter()
    for p in pillars:
        counts[p['gan_element']] += 1
        counts[p['zhi_element']] += 1
    counts = {element: counts.get(element, 0) for element in '木火土金水'}
    min_count = min(counts.values())
    underrepresented = [k for k, v in counts.items() if v == min_count]
    suggestions = [dict(element=e, **ELEMENT_LIFESTYLE[e]) for e in underrepresented[:2]]
    ten_gods = _ten_god_summary(pillars)

    yun = ec.getYun(1 if gender == '男' else 0, 2)
    dayun_items = []
    current_cycles = None
    for dy in yun.getDaYun(dayun_count + 1):
        if dy.getIndex() == 0:
            continue
        gz = dy.getGanZhi()
        liunian = dy.getLiuNian(10)
        xiaoyun = dy.getXiaoYun(10)
        years = []
        for ln, xy in zip(liunian, xiaoyun):
            item = {
                'year': ln.getYear(), 'age': ln.getAge(),
                'liunian': ln.getGanZhi(), 'xiaoyun': xy.getGanZhi(),
            }
            years.append(item)
            if target_year and ln.getYear() == target_year:
                current_cycles = {'dayun': gz, **item}
        dayun_items.append({
            'ganzhi': gz, 'start_age': dy.getStartAge(), 'end_age': dy.getEndAge(),
            'start_year': dy.getStartYear(), 'end_year': dy.getEndYear(),
            'xunkong': dy.getXunKong(),
            'shen_sha': common_shensha(day_gan, day_zhi, year_zhi, gz[1]),
            'years': years,
        })

    return {
        'calculation_basis': 'lunar-python；四柱按节气月；日柱 sect=2；起运按分钟法 sect=2',
        'solar_datetime': lunar.getSolar().toYmdHms(),
        'lunar_date': lunar.toString(),
        'pillars_text': ec.toString(),
        'day_master': day_gan,
        'day_master_element': GAN_ELEMENT[day_gan],
        'zodiac': ZODIAC[year_zhi],
        'year_ganzhi': pillars[0]['ganzhi'],
        'year_nayin': pillars[0]['nayin'],
        'ten_god_summary': ten_gods,
        'pillars': pillars,
        'five_elements_count': counts,
        'underrepresented_elements': underrepresented,
        'element_suggestions': suggestions,
        'element_note': '只统计四柱八个显性干支，不含藏干权重；数量多少不等同于喜用神。',
        'tai_yuan': ec.getTaiYuan(), 'tai_xi': ec.getTaiXi(),
        'ming_gong': ec.getMingGong(), 'shen_gong': ec.getShenGong(),
        'yun': {
            'forward': yun.isForward(),
            'start': {'year': yun.getStartYear(), 'month': yun.getStartMonth(),
                      'day': yun.getStartDay(), 'solar': yun.getStartSolar().toYmdHms()},
            'dayun': dayun_items,
            'current': current_cycles,
        },
        'bone_weight': _bone_weight(lunar, ec),
        'limits': {
            'children': '只讨论子女缘、亲子互动和阶段性倾向；不预测准确数量、胎儿性别或生育结果。',
            'relationship': '只给候选缘分窗口和关系场景，不承诺某年必遇正缘或必然结婚。',
            'lifestyle': '方位、颜色、发型、车色和休闲活动仅作传统五行审美灵感。',
        },
    }
