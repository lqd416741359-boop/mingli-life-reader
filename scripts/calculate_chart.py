#!/usr/bin/env python3
"""紫微斗数排盘计算脚本

基于 iztro-py 库，输入生辰信息，输出精确的十二宫星曜分布数据。
输出 JSON 格式，供 HTML 模板和 LLM 解读使用。

V2.1 新增（合并社区共创版机制）:
  - 空宫借星安宫与能量降阶标记 (reduce_empty_palaces)
  - 宏观格局判定与三维量化 (evaluate_gezhi)
  - 流年/大限化忌叠冲追踪 (track_time_mutagens)
  - --year 参数指定目标流年（默认当前年份，不再硬编码）

用法:
    python3 calculate_chart.py --solar 1991-8-15 --hour 1 --gender 男
    python3 calculate_chart.py --lunar 1991-7-6 --hour 1 --gender 男 --leap
    python3 calculate_chart.py --solar 1991-8-15 --hour 1 --gender 男 --year 2027
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gezhi_rules import reduce_empty_palaces, evaluate_gezhi, track_time_mutagens
from bazi_calculator import calculate_bazi

BRANCH_CN = {
    'ziEarthly': '子', 'chouEarthly': '丑', 'yinEarthly': '寅',
    'maoEarthly': '卯', 'chenEarthly': '辰', 'siEarthly': '巳',
    'wuEarthly': '午', 'weiEarthly': '未', 'shenEarthly': '申',
    'youEarthly': '酉', 'xuEarthly': '戌', 'haiEarthly': '亥',
}

STEM_CN = {
    'jiaHeavenly': '甲', 'yiHeavenly': '乙', 'bingHeavenly': '丙',
    'dingHeavenly': '丁', 'wuHeavenly': '戊', 'jiHeavenly': '己',
    'gengHeavenly': '庚', 'xinHeavenly': '辛', 'renHeavenly': '壬',
    'guiHeavenly': '癸',
}

FIVE_ELEMENTS_CN = {
    'water2': '水二局', 'wood3': '木三局', 'metal4': '金四局',
    'earth5': '土五局', 'fire6': '火六局',
}

MUTAGEN_CN = {'禄': '化禄', '权': '化权', '科': '化科', '忌': '化忌'}


def translate_name(obj):
    if hasattr(obj, 'translate_name'):
        return obj.translate_name()
    return str(obj)


def build_chart(date_str, hour_index, gender, is_lunar=False, is_leap=False, language='zh-CN'):
    from iztro_py import astro

    if is_lunar:
        chart = astro.by_lunar(date_str, hour_index, gender, is_leap, True, language)
    else:
        chart = astro.by_solar(date_str, hour_index, gender, language)

    soul_idx = chart.get_soul_palace().index
    body_idx = chart.get_body_palace().index

    # 五行局
    fec = chart.five_elements_class
    five_elements = FIVE_ELEMENTS_CN.get(fec, fec)

    # 四化（生年四化）
    year_mutagens = []
    for p in chart.palaces:
        for s in list(p.major_stars) + list(p.minor_stars):
            if hasattr(s, 'mutagen') and s.mutagen:
                year_mutagens.append({
                    'star': translate_name(s),
                    'mutagen': MUTAGEN_CN.get(s.mutagen, s.mutagen),
                    'palace': translate_name(p),
                    'branch': BRANCH_CN.get(p.earthly_branch, p.earthly_branch),
                })

    # 十二宫数据
    palaces = []
    for p in chart.palaces:
        major = [translate_name(s) for s in p.major_stars]
        minor = [translate_name(s) for s in p.minor_stars]
        adj = [translate_name(s) for s in p.adjective_stars] if hasattr(p, 'adjective_stars') else []

        star_mutagens = []
        for s in list(p.major_stars) + list(p.minor_stars):
            if hasattr(s, 'mutagen') and s.mutagen:
                star_mutagens.append({
                    'star': translate_name(s),
                    'mutagen': s.mutagen,
                })

        dec = p.decadal
        decadal_range = f"{dec.range[0]}-{dec.range[1]}" if dec else ""
        decadal_stem = STEM_CN.get(dec.heavenly_stem, dec.heavenly_stem) if dec else ""
        decadal_branch = BRANCH_CN.get(dec.earthly_branch, dec.earthly_branch) if dec else ""

        is_empty = not major
        tags = []
        if p.index == soul_idx:
            tags.append('命宫')
        if p.index == body_idx:
            tags.append('身宫')

        palace_data = {
            'name': translate_name(p),
            'heavenly_stem': STEM_CN.get(p.heavenly_stem, p.heavenly_stem),
            'earthly_branch': BRANCH_CN.get(p.earthly_branch, p.earthly_branch),
            'dizhi': STEM_CN.get(p.heavenly_stem, '') + BRANCH_CN.get(p.earthly_branch, ''),
            'major_stars': major,
            'minor_stars': minor,
            'adjective_stars': adj[:5],
            'mutagens': star_mutagens,
            'is_empty': is_empty,
            'decadal_range': decadal_range,
            'decadal_dizhi': decadal_stem + decadal_branch,
            'tags': tags,
            'index': p.index,
        }
        palaces.append(palace_data)

    # 空宫列表
    empty_palaces_result = chart.empty_palaces() if callable(getattr(chart, 'empty_palaces', None)) else []
    empty_palaces = [BRANCH_CN.get(ep.earthly_branch, str(ep)) for ep in empty_palaces_result]

    # 公历/农历日期（两种输入下都从引擎取规范值，避免 lunar 输入时 solar_date 为空）
    solar_date = date_str if not is_lunar else getattr(chart, 'solar_date', None)
    lunar_date = date_str if is_lunar else getattr(chart, 'lunar_date', None)

    result = {
        'solar_date': solar_date,
        'lunar_date': lunar_date,
        'birth_year': int(str(solar_date).split('-')[0]) if solar_date else None,
        'chinese_date': chart.chinese_date,
        'gender': gender,
        'hour_index': hour_index,
        'five_elements': five_elements,
        'soul_palace_branch': BRANCH_CN.get(chart.earthly_branch_of_soul_palace, chart.earthly_branch_of_soul_palace),
        'body_palace_branch': BRANCH_CN.get(chart.earthly_branch_of_body_palace, chart.earthly_branch_of_body_palace),
        'year_mutagens': year_mutagens,
        'empty_palaces': empty_palaces,
        'palaces': palaces,
    }
    return result


def enrich_chart(chart, target_year):
    """V2 后处理管线：空宫降阶 → 格局扫描 → 时空压力审计"""
    reduce_empty_palaces(chart)
    chart['gezhi_analysis'] = evaluate_gezhi(chart)
    chart['time_travel_analysis'] = track_time_mutagens(chart, current_year=target_year)
    return chart


HOUR_NAMES = {
    0: '早子时 (23:00-00:00)', 1: '丑时 (01:00-03:00)',
    2: '寅时 (03:00-05:00)', 3: '卯时 (05:00-07:00)',
    4: '辰时 (07:00-09:00)', 5: '巳时 (09:00-11:00)',
    6: '午时 (11:00-13:00)', 7: '未时 (13:00-15:00)',
    8: '申时 (15:00-17:00)', 9: '酉时 (17:00-19:00)',
    10: '戌时 (19:00-21:00)', 11: '亥时 (21:00-23:00)',
    12: '晚子时 (23:00-00:00)',
}


def main():
    parser = argparse.ArgumentParser(description='紫微斗数排盘计算')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--solar', help='阳历日期，格式 YYYY-M-D')
    group.add_argument('--lunar', help='农历日期，格式 YYYY-M-D')
    parser.add_argument('--hour', type=int, required=True,
                        help='时辰索引: 0=早子 1=丑 2=寅 ... 11=亥 12=晚子')
    parser.add_argument('--gender', required=True, choices=['男', '女'])
    parser.add_argument('--leap', action='store_true', help='农历闰月（仅 --lunar 有效）')
    parser.add_argument('--year', type=int, default=datetime.date.today().year,
                        help='目标流年年份（默认当前年份），用于时空压力审计')
    parser.add_argument('--output', help='输出文件路径（默认 stdout）')

    args = parser.parse_args()

    is_lunar = args.lunar is not None
    date_str = args.lunar if is_lunar else args.solar

    chart = build_chart(date_str, args.hour, args.gender, is_lunar, args.leap)
    chart['bazi_analysis'] = calculate_bazi(
        date_str=date_str,
        hour_index=args.hour,
        gender=args.gender,
        is_lunar=is_lunar,
        is_leap=args.leap,
        target_year=args.year,
    )
    chart = enrich_chart(chart, args.year)

    output = json.dumps(chart, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f'排盘数据已写入: {args.output}')
    else:
        print(output)


if __name__ == '__main__':
    main()
