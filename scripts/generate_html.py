#!/usr/bin/env python3
"""HTML 命盘生成脚本

读取排盘数据 JSON + 解读文字，填充 HTML 模板，输出最终命盘文件。

V2.1 说明（合并社区共创版机制，拆除外部话术依赖）:
  - 空宫借星渲染 + 能量系数标签（依赖 calculate_chart.py 的后处理字段）
  - 第 0 章「宏观格局仪表盘」: 由 chart.json 的 gezhi_analysis 纯数据渲染，自动插入 cards 头部
  - 第 6 章「时空压力热力表」: 由 time_travel_analysis 纯数据渲染，干支动态计算，自动追加 cards 尾部
  - 不再依赖任何外部话术模块；解读文案一律由 LLM 写入 reading.json
  - reading.json 为空结构时也能出完整 HTML（第 0/6 章自动注入）

用法:
    python3 generate_html.py --chart chart_data.json --reading reading.json --output mingpan.html
"""
import argparse
import html
import json
import os
import sys

from report_structure import (
    CHAPTER_ORDER,
    ReadingStructureError,
    normalize_reading,
    require_valid_v2_reading,
)

HOUR_NAMES_MAP = {
    0: '早子时', 1: '丑时', 2: '寅时', 3: '卯时',
    4: '辰时', 5: '巳时', 6: '午时', 7: '未时',
    8: '申时', 9: '酉时', 10: '戌时', 11: '亥时', 12: '晚子时',
}

# 宫位在 4x4 网格中的排列顺序（外圈顺时针）
# Row 1: 巳(0) 午(1) 未(2) 申(3)
# Row 2: 辰(11) [center] [center] 酉(4)
# Row 3: 卯(10) [center] [center] 戌(5)
# Row 4: 寅(9) 丑(8) 子(7) 亥(6)
BRANCH_GRID_MAP = {
    '巳': (1, 1), '午': (1, 2), '未': (1, 3), '申': (1, 4),
    '辰': (2, 1),                          '酉': (2, 4),
    '卯': (3, 1),                          '戌': (3, 4),
    '寅': (4, 1), '丑': (4, 2), '子': (4, 3), '亥': (4, 4),
}


def build_palace_cell(p, soul_branch, body_branch, current_decadal_branch):
    branch = p['earthly_branch']
    name = p['name']
    major = p['major_stars']
    minor = p['minor_stars']
    mutagens = p.get('mutagens', [])

    # 检测空宫元数据（由 gezhi_rules.reduce_empty_palaces 注入）
    is_empty = p.get("is_empty_palace", False)
    coef = p.get("energy_coefficient", 1.0)
    borrowed_major = p.get("borrowed_major_stars", [])
    borrowed_minor = p.get("borrowed_minor_stars", [])

    classes = ['palace']
    if branch == soul_branch:
        classes.append('active')
    if branch == current_decadal_branch:
        classes.append('current-limit')
    if is_empty:
        classes.append('empty-palace')

    stars_html = ''
    if is_empty:
        # 空宫：渲染借星，带特殊样式
        for s in borrowed_major:
            stars_html += f'<span class="star main borrowed-star">{s}</span>\n'
        for s in borrowed_minor:
            stars_html += f'<span class="star borrowed-star">{s}</span>\n'
        if not borrowed_major and not borrowed_minor:
            stars_html = '<span class="star empty">空宫</span>\n'
    elif major:
        for s in major:
            mut = next((m['mutagen'] for m in mutagens if m['star'] == s), None)
            if mut:
                stars_html += f'<span class="star main">{s}</span>\n'
                stars_html += f'<span class="star four-hua">{s}{mut}</span>\n'
            else:
                stars_html += f'<span class="star main">{s}</span>\n'
        for s in minor:
            mut = next((m['mutagen'] for m in mutagens if m['star'] == s), None)
            if mut:
                stars_html += f'<span class="star">{s}</span>\n'
                stars_html += f'<span class="star four-hua">{s}{mut}★</span>\n'
            else:
                stars_html += f'<span class="star">{s}</span>\n'
    else:
        stars_html = '<span class="star empty">空宫</span>\n'

    badges = ''
    for tag in p.get('tags', []):
        if tag == '命宫':
            badges += '<div class="palace-badge badge-ming">命宫</div>\n'
        elif tag == '身宫':
            badges += '<div class="palace-badge badge-body">身宫</div>\n'

    if branch == current_decadal_branch and '命宫' not in p.get('tags', []) and '身宫' not in p.get('tags', []):
        badges += '<div class="palace-badge badge-limit">当前大限</div>\n'

    # 空宫元数据标签
    if is_empty:
        vuln_cls = 'vuln-high' if coef == 0.5 else 'vuln-medium'
        meta_html = f'''<div class="palace-meta-badge">
            <span class="badge-tag borrowed-tag">借星安宫</span>
            <span class="badge-coef {vuln_cls}">能量系数 {coef}</span>
        </div>'''
    else:
        meta_html = '<div class="palace-meta-badge"><span class="badge-coef stable">能量系数 1.0</span></div>'

    return f'''<div class="{' '.join(classes)}">
      <div class="palace-name">{name}</div>
      <div class="palace-dizhi">{branch}</div>
      <div class="palace-stars">{stars_html}</div>
      {badges}
      {meta_html}
    </div>'''


def build_palace_grid(palaces, soul_branch, body_branch, current_decadal_branch):
    grid = {}
    for p in palaces:
        branch = p['earthly_branch']
        if branch in BRANCH_GRID_MAP:
            row, col = BRANCH_GRID_MAP[branch]
            grid[(row, col)] = build_palace_cell(p, soul_branch, body_branch, current_decadal_branch)

    cells = []
    for row in range(1, 5):
        for col in range(1, 5):
            if row in (2, 3) and col in (2, 3):
                continue  # center area
            cell = grid.get((row, col), '<div class="palace"></div>')
            cells.append(cell)

    return '\n    '.join(cells)


def build_four_hua_tags(year_mutagens):
    mutagen_classes = {
        '化禄': 'hua-lu', '化权': 'hua-quan',
        '化科': 'hua-ke', '化忌': 'hua-ji',
    }
    tags = []
    for m in year_mutagens:
        cls = mutagen_classes.get(m['mutagen'], '')
        tags.append(f'<span class="hua-tag {cls}">{m["star"]}{m["mutagen"]}</span>')
    return '\n        '.join(tags)


def build_reading_cards(reading):
    cn_nums = ['一', '二', '三', '四', '五', '六', '七']
    cards = []
    for i, card in enumerate(reading.get('cards', [])):
        num = cn_nums[i] if i < len(cn_nums) else str(i + 1)
        classes = ['reading-card']
        if card.get('full'):
            classes.append('full')
        if card.get('highlight'):
            classes.append('highlight')
        if card.get('teal'):
            classes.append('teal-highlight')

        prob_html = ''
        if card.get('probabilities'):
            for pb in card['probabilities']:
                prob_html += f'''<div class="prob-bar">
                    <span class="prob-label">{pb['label']}</span>
                    <div class="prob-track"><div class="prob-fill" style="width:{pb['pct']}%"></div></div>
                    <span class="prob-pct">{pb['pct']}%</span>
                </div>\n'''

        cards.append(f'''<div class="{' '.join(classes)}" data-num="{num}">
      <div class="card-title">{card['title']}</div>
      <div class="card-stars-badge">{card.get('badge', '')}</div>
      <div class="card-body">{card['body']}</div>
      {f'<div style="margin-top:16px;">{prob_html}</div>' if prob_html else ''}
    </div>''')

    return '\n    '.join(cards)


def _escaped_list(items):
    return ''.join(f'<li>{html.escape(str(item))}</li>' for item in items)


def build_overview(overview):
    """渲染 V2 一分钟摘要。"""
    title = html.escape(str(overview.get('title') or '一分钟看懂'))
    return f'''<section class="overview-panel">
      <h2>{title}</h2>
      <ul>{_escaped_list(overview.get('items', []))}</ul>
    </section>'''


def build_chapters(chapters):
    """按固定顺序渲染 V2 十章，所有解读文字均作 HTML 转义。"""
    rendered = []
    for number, key in enumerate(CHAPTER_ORDER, 1):
        chapter = chapters[key]
        evidence = chapter.get('evidence', {})
        if isinstance(evidence, dict):
            evidence_html = ''.join(
                f'<p><b>{html.escape(str(label))}：</b>{html.escape(str(value))}</p>'
                for label, value in evidence.items()
            )
        else:
            evidence_html = f'<p>{html.escape(str(evidence))}</p>'
        rendered.append(f'''<article class="life-chapter" data-chapter="{key}">
          <div class="chapter-number">{number:02d}</div>
          <h2>{html.escape(str(chapter.get('title') or key))}</h2>
          <p class="chapter-verdict">{html.escape(str(chapter['verdict']))}</p>
          <h3>现实表现</h3><ul>{_escaped_list(chapter['manifestations'])}</ul>
          <h3>优势与机会</h3><ul>{_escaped_list(chapter['strengths'])}</ul>
          <h3>容易踩的坑</h3><ul>{_escaped_list(chapter['pitfalls'])}</ul>
          <h3>可以怎么做</h3><ul>{_escaped_list(chapter['actions'])}</ul>
          <details class="chapter-evidence"><summary>查看专业依据</summary>{evidence_html}</details>
        </article>''')
    return '\n'.join(rendered)


def build_hand_section(hand_data):
    if not hand_data or not hand_data.get('items'):
        return ''

    cards_html = ''
    for item in hand_data['items']:
        conflict_tag = ''
        if item.get('status') == 'match':
            conflict_tag = f'<div class="conflict-tag match">{item["status_text"]}</div>'
        elif item.get('status') == 'conflict':
            conflict_tag = f'<div class="conflict-tag conflict">{item["status_text"]}</div>'
            if item.get('resolution'):
                conflict_tag += f'<div style="font-size:11px;color:var(--ivory-dim);margin-top:6px;line-height:1.7;">取舍：{item["resolution"]}</div>'

        cards_html += f'''<div class="hand-card">
        <div class="hand-card-title">{item['title']}</div>
        <div class="hand-card-body">{item['body']}</div>
        {conflict_tag}
      </div>\n'''

    return f'''<div class="section-title">手相互证</div>
  <div class="hand-section">
    <div class="hand-grid">{cards_html}</div>
    </div>'''


def build_sanshishu_html(sections):
    """渲染经过安全改写的三世书条目。"""
    if not sections:
        return ''
    items = []
    for section in sections:
        title = html.escape(str(section.get('title', '传统条目')))
        traditional = html.escape(str(section.get('traditional', '')))
        plain = html.escape(str(section.get('plain', '')))
        advice = html.escape(str(section.get('advice', '')))
        notice = html.escape(str(section.get('notice', '传统民俗寓言，仅供文化阅读。')))
        items.append(f'''<article class="sanshi-card">
          <h3>{title}</h3>
          <p><b>传统意象：</b>{traditional}</p>
          <p><b>白话解释：</b>{plain}</p>
          <p><b>现实建议：</b>{advice}</p>
          <small>{notice}</small>
        </article>''')
    return f'''<div class="section-title">三世书 · 民俗条目白话解读</div>
      <section class="sanshi-section">{''.join(items)}</section>'''


def build_calibration(questions):
    cn_nums = ['一', '二', '三', '四', '五']
    html = ''
    for i, q in enumerate(questions[:5]):
        num = cn_nums[i] if i < len(cn_nums) else str(i + 1)
        hint = f'<span>{q["hint"]}</span>' if q.get('hint') else ''
        html += f'''<div class="cal-q">
        <div class="cal-num">{num}</div>
        <div class="cal-text">{q['text']}{hint}</div>
      </div>\n'''
    return html


def build_bazi_section(bazi):
    """渲染四柱、五行、大运流年小运、神煞与称骨。"""
    if not bazi:
        return ''

    def esc(value):
        return html.escape(str(value or ''))

    pillar_rows = ''
    for p in bazi.get('pillars', []):
        shensha = '、'.join(p.get('shen_sha', [])) or '—'
        hidden = '、'.join(p.get('hidden_stems', [])) or '—'
        ten_zhi = '、'.join(p.get('ten_god_zhi', [])) or '—'
        pillar_rows += f'''<tr>
          <th>{esc(p['name'])}</th>
          <td class="ganzhi-big">{esc(p['ganzhi'])}</td>
          <td>{esc(p['gan_element'])}／{esc(p['zhi_element'])}</td>
          <td>{esc(p['ten_god_gan'])}<br><small>{esc(ten_zhi)}</small></td>
          <td>{esc(hidden)}</td>
          <td>{esc(p['nayin'])}</td>
          <td>{esc(p['dishi'])}</td>
          <td>{esc(p['xunkong'])}</td>
          <td>{esc(shensha)}</td>
        </tr>'''

    counts = bazi.get('five_elements_count', {})
    max_count = max([int(v) for v in counts.values()] or [1])
    element_bars = ''
    for element in '木火土金水':
        count = int(counts.get(element, 0))
        width = int(count / max_count * 100) if max_count else 0
        element_bars += f'''<div class="element-row element-{element}">
          <span>{element}</span><div class="element-track"><i style="width:{width}%"></i></div><b>{count}</b>
        </div>'''

    inspiration = ''
    for item in bazi.get('element_suggestions', []):
        inspiration += f'''<div class="inspiration-card">
          <h4>{esc(item['element'])} · 生活灵感</h4>
          <p><b>方向：</b>{esc('、'.join(item['directions']))}</p>
          <p><b>配色：</b>{esc('、'.join(item['colors']))}</p>
          <p><b>职业环境：</b>{esc('、'.join(item['careers']))}</p>
          <p><b>休闲活动：</b>{esc('、'.join(item['leisure']))}</p>
        </div>'''

    dayun_blocks = ''
    current = bazi.get('yun', {}).get('current') or {}
    for dy in bazi.get('yun', {}).get('dayun', []):
        years = ''
        for y in dy.get('years', []):
            current_cls = ' class="current-year"' if y.get('year') == current.get('year') else ''
            years += f'''<tr{current_cls}><td>{y['year']}</td><td>{y['age']}岁</td>
              <td>{esc(y['liunian'])}</td><td>{esc(y['xiaoyun'])}</td></tr>'''
        shensha = '、'.join(dy.get('shen_sha', [])) or '—'
        dayun_blocks += f'''<details class="dayun-block">
          <summary><b>{esc(dy['ganzhi'])}</b> · {dy['start_age']}–{dy['end_age']}岁
            <span>{dy['start_year']}–{dy['end_year']} · 神煞 {esc(shensha)}</span></summary>
          <table class="cycle-table"><tr><th>年份</th><th>年龄</th><th>流年</th><th>小运</th></tr>{years}</table>
        </details>'''

    bone = bazi.get('bone_weight', {})
    ten_gods = bazi.get('ten_god_summary', {})
    ten_god_cards = ''
    for profile in ten_gods.get('dominant_profiles', []):
        ten_god_cards += f'''<div class="inspiration-card">
          <h4>{esc(profile.get('name'))} · {esc(profile.get('label'))}</h4>
          <p>{esc(profile.get('plain'))}</p><p class="method-note">盘中统计：{profile.get('count', 0)}处</p>
        </div>'''
    parts = bone.get('breakdown_qian', {})
    current_line = ''
    if current:
        current_line = (f"当前参考：大运 <b>{esc(current.get('dayun'))}</b> · "
                        f"{current.get('year')}年流年 <b>{esc(current.get('liunian'))}</b> · "
                        f"小运 <b>{esc(current.get('xiaoyun'))}</b>")

    return f'''<section class="bazi-section">
      <div class="section-title">四柱八字 · 基础命盘</div>
      <div class="bazi-intro">
        <div><span>生肖／出生年</span><strong>属{esc(bazi.get('zodiac'))} · {esc(bazi.get('year_ganzhi'))}年</strong></div>
        <div><span>年柱纳音</span><strong>{esc(bazi.get('year_nayin'))}</strong></div>
        <div><span>日主五行</span><strong>{esc(bazi.get('day_master'))}{esc(bazi.get('day_master_element'))}</strong></div>
        <div><span>八字命格入门标签</span><strong>{esc(ten_gods.get('pattern_name'))}</strong></div>
      </div>
      <div class="paper-card destiny-card">
        <h3>{esc(ten_gods.get('pattern_name'))} · {esc(ten_gods.get('plain_label'))}</h3>
        <p>{esc(ten_gods.get('plain_explanation'))}</p>
        <p class="method-note">依据：{esc(ten_gods.get('pattern_basis'))}。{esc(ten_gods.get('disclaimer'))}</p>
        <div class="inspiration-grid">{ten_god_cards}</div>
      </div>
      <div class="table-scroll"><table class="bazi-table">
        <tr><th>四柱</th><th>干支</th><th>五行</th><th>十神</th><th>藏干</th><th>纳音</th><th>地势</th><th>空亡</th><th>常用神煞</th></tr>
        {pillar_rows}
      </table></div>

      <div class="bazi-two-col">
        <div class="paper-card">
          <h3>显性五行数量</h3>{element_bars}
          <p class="method-note">{esc(bazi.get('element_note'))}</p>
        </div>
        <div class="paper-card">
          <h3>五行生活灵感</h3><div class="inspiration-grid">{inspiration}</div>
          <p class="method-note">方向、穿搭、发型与车色只作象征性审美参考；安全、职业机会和个人喜好优先。</p>
        </div>
      </div>

      <div class="paper-card cycle-card">
        <h3>大运 · 流年 · 小运</h3>
        <p>{current_line or '目标年份不在当前展示范围内。'}</p>
        <p class="method-note">起运：{esc(bazi.get('yun', {}).get('start', {}).get('solar'))}；
          {'顺排' if bazi.get('yun', {}).get('forward') else '逆排'}。展开各大运可看逐年流年与小运。</p>
        <div class="dayun-list">{dayun_blocks}</div>
      </div>

      <div class="paper-card bone-card">
        <h3>袁天罡称骨歌 · 民俗附录</h3>
        <div class="bone-weight">{esc(bone.get('display'))}</div>
        <p>年 {parts.get('year', 0)}钱 ＋ 月 {parts.get('month', 0)}钱 ＋ 日 {parts.get('day', 0)}钱 ＋ 时 {parts.get('hour', 0)}钱</p>
        <blockquote>{esc(bone.get('poem'))}</blockquote>
        <div class="bone-explanation">
          <h4>{esc(bone.get('plain_title'))}</h4>
          <p>{esc(bone.get('plain_explanation'))}</p>
        </div>
        <p class="method-note">{esc(bone.get('version'))}。{esc(bone.get('disclaimer'))}</p>
      </div>
    </section>'''


def build_gezhi_dashboard_card(gezhi):
    """第 0 章: 宏观格局仪表盘（纯数据渲染，无外部话术依赖）"""
    if not gezhi:
        return None
    metrics = gezhi.get('quant_metrics', {
        'risk_tolerance': 3, 'fluctuation_resilience': 3, 'decision_aggressiveness': 3
    })
    warnings_html = ''
    for w in gezhi.get('stress_warnings', []):
        warnings_html += f'<p class="warn" style="margin-top:10px;">⚠ {w["type"]}：{w["desc"]}</p>'

    detail_html = ''
    if gezhi.get('plain_summary'):
        detail_html = f"""<div class="gezhi-explain">
          <p class="plain-summary">{gezhi.get('plain_summary', '')}</p>
          <div class="gezhi-detail-grid">
            <div><b>擅长什么</b><p>{gezhi.get('strengths', '')}</p></div>
            <div><b>现代职业环境</b><p>{gezhi.get('modern_roles', '')}</p></div>
            <div><b>容易卡在哪里</b><p>{gezhi.get('pitfalls', '')}</p></div>
          </div>
          <p class="formation-note">判定口径：{gezhi.get('formation_note', '')}</p>
        </div>"""

    dashboard_body = f"""<div class="gezhi-dashboard">
        <h3>格局判定: <strong>{gezhi.get('gezhi_name', '')}</strong></h3>
        <p class="tech-alias">{gezhi.get('tech_alias', '')}</p>
        <p class="desc">{gezhi.get('description', '')}</p>
        {detail_html}
        <hr style="border:0;border-top:1px solid rgba(128,128,128,0.25);margin:15px 0;"/>
        <div class="metrics-container">
            <div class="metric-line">系统风险耐受度: <strong>{metrics['risk_tolerance']}/5</strong>
                <div class="bar"><div class="fill" style="width:{metrics['risk_tolerance']*20}%"></div></div>
            </div>
            <div class="metric-line">逆境波动恢复力: <strong>{metrics['fluctuation_resilience']}/5</strong>
                <div class="bar"><div class="fill" style="width:{metrics['fluctuation_resilience']*20}%;background:#2f9e44;"></div></div>
            </div>
            <div class="metric-line">决策激进度: <strong>{metrics['decision_aggressiveness']}/5</strong>
                <div class="bar"><div class="fill" style="width:{metrics['decision_aggressiveness']*20}%"></div></div>
            </div>
        </div>
        {warnings_html}
    </div>"""
    return {
        "title": "宏观格局 · 先天禀赋量化",
        "badge": gezhi.get('gezhi_name', ''),
        "full": True,
        "highlight": True,
        "body": dashboard_body
    }


def build_time_travel_card(tta):
    """第 6 章: 时空压力热力表（纯数据渲染，干支动态取自排盘结果，无外部话术依赖）"""
    if not tta:
        return None

    year = tta.get('target_year', '')
    stem = tta.get('liunian_stem', '')
    branch = tta.get('liunian_branch', '')
    liunian_ji = tta.get('liunian_ji_star') or '—'
    daxian_ji = tta.get('daxian_ji_star') or '—'
    daxian_palace = tta.get('current_decadal_palace') or '—'

    rows_html = ''
    for item in tta.get('full_time_log', []):
        score = item['stress_score']
        row_cls = 'row-hotspot' if item.get('is_hotspot') else ('row-warn' if score >= 1.5 else '')
        tag_cls = 'score-hot' if item.get('is_hotspot') else ('score-high' if score >= 1.5 else '')
        sources = '；'.join(item.get('trigger_sources', []))
        rows_html += f'''<tr class="{row_cls}">
            <td>{item['palace_name']} <span class="branch-td">{item['earthly_branch']}</span></td>
            <td><span class="score-tag {tag_cls}">{score}</span></td>
            <td class="risk-td">{item['risk_level']}</td>
            <td class="risk-td">{sources}</td>
        </tr>\n'''

    body_html = f"""<div class="time-travel-panel">
        <h4>{year}年 {stem}{branch} · 时空压力审计</h4>
        <p class="tech-alias">流年化忌 [{liunian_ji}] · 大限化忌 [{daxian_ji}] · 当前大限 [{daxian_palace}]（生年忌宫：{tta.get('birth_year_ji_branch') or '—'}）</p>
        <table class="stress-table">
            <tr><th>检测宫位</th><th>压力分值</th><th>风险评级</th><th>触发源追踪</th></tr>
            {rows_html}
        </table>
        <p class="risk-td" style="margin-top:12px;">压力分 ≥2.5 为高危热点，≥1.5 为预警；得分由生年化忌（对宫冲射 ×1.5 加权）与大限/流年叠忌累计。</p>
    </div>"""

    return {
        "title": f"时空压力审计 · {year}年叠忌扫描",
        "badge": f"{stem}{branch}年",
        "full": True,
        "teal": True,
        "body": body_html
    }


def generate_html(chart_data, reading_data, template_path):
    reading_data = normalize_reading(reading_data)
    if reading_data['format'] == 'v2':
        require_valid_v2_reading(reading_data)

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    soul_branch = chart_data['soul_palace_branch']
    body_branch = chart_data['body_palace_branch']

    # Find soul palace stars
    soul_palace = next((p for p in chart_data['palaces'] if '命宫' in p.get('tags', [])), None)
    soul_stars = '·'.join(soul_palace['major_stars']) if soul_palace and soul_palace['major_stars'] else '空宫（借对宫星曜）'

    hour_name = HOUR_NAMES_MAP.get(chart_data['hour_index'], '丑时')

    # Determine current decadal palace
    current_decadal_branch = ''
    if reading_data.get('current_decadal_branch'):
        current_decadal_branch = reading_data['current_decadal_branch']
    elif chart_data.get('time_travel_analysis', {}).get('current_decadal_palace'):
        # 排盘数据自带当前大限宫位，兜底取它的地支
        palace_name = chart_data['time_travel_analysis']['current_decadal_palace']
        palace = next((p for p in chart_data['palaces'] if p['name'] == palace_name), None)
        if palace:
            current_decadal_branch = palace['earthly_branch']
            reading_data.setdefault('current_decadal_display',
                                    f"{palace['dizhi']}（{palace['decadal_range']}大限）")

    # Build palace grid
    palace_cells = build_palace_grid(
        chart_data['palaces'], soul_branch, body_branch, current_decadal_branch
    )

    # Build four hua tags
    four_hua_tags = build_four_hua_tags(chart_data['year_mutagens'])

    # ========================================================
    # 章节组装: [第0章 格局仪表盘] → [LLM 解读卡片] → [第6章 时空压力表]
    # ========================================================
    cards_list = list(reading_data.get("cards", []))

    gezhi_card = build_gezhi_dashboard_card(chart_data.get('gezhi_analysis'))
    if gezhi_card:
        cards_list.insert(0, gezhi_card)

    tta_card = build_time_travel_card(chart_data.get('time_travel_analysis'))
    if tta_card:
        cards_list.append(tta_card)

    if reading_data['format'] == 'v2':
        reading_cards = build_overview(reading_data['overview'])
        reading_cards += build_chapters(reading_data['chapters'])
        if cards_list:
            reading_cards += build_reading_cards({'cards': cards_list})
    else:
        reading_data['cards'] = cards_list
        reading_cards = build_reading_cards(reading_data)

    # Build hand section
    hand_section = build_hand_section(reading_data.get('hand_reading'))

    # Optional folklore appendix, already softened before rendering.
    sanshishu_section = build_sanshishu_html(reading_data.get('sanshishu_sections', []))

    # Build calibration
    calibration = build_calibration(reading_data.get('calibration_questions', []))

    # Build deterministic Four Pillars / BaZi appendix
    bazi_section = build_bazi_section(chart_data.get('bazi_analysis'))

    # Date info
    solar = chart_data.get('solar_date', '')
    lunar = chart_data.get('lunar_date', '')
    chinese = chart_data.get('chinese_date', '')

    # Extract year stem/branch from chinese_date
    parts = chinese.split() if chinese else []
    year_sb = parts[0] if parts else ''
    year_stem_char = year_sb[0] if len(year_sb) >= 2 else ''
    year_branch_char = year_sb[1] if len(year_sb) >= 2 else ''

    date_info = f'公历 {solar}' if solar else ''
    lunar_info = f'农历 {lunar}' if lunar else ''

    replacements = {
        '{{YEAR_STEM}}': year_stem_char,
        '{{YEAR_BRANCH}}': year_branch_char,
        '{{HOUR_NAME}}': hour_name,
        '{{LUNAR_DATE}}': lunar,
        '{{GENDER}}': chart_data['gender'],
        '{{FIVE_ELEMENTS}}': chart_data['five_elements'],
        '{{SOUL_PALACE_BRANCH}}': soul_branch,
        '{{SOUL_PALACE_STARS}}': soul_stars,
        '{{CURRENT_DECADAL}}': reading_data.get('current_decadal_display', ''),
        '{{PALACE_CELLS}}': palace_cells,
        '{{FOUR_HUA_TAGS}}': four_hua_tags,
        '{{DATE_INFO}}': date_info,
        '{{LUNAR_INFO}}': lunar_info,
        '{{BAZI_SECTION}}': bazi_section,
        '{{READING_CARDS}}': reading_cards,
        '{{HAND_SECTION}}': hand_section,
        '{{SANSHISHU_SECTION}}': sanshishu_section,
        '{{CALIBRATION_QUESTIONS}}': calibration,
    }

    html = template
    for key, val in replacements.items():
        html = html.replace(key, str(val))

    return html


def main():
    parser = argparse.ArgumentParser(description='命盘 HTML 生成')
    parser.add_argument('--chart', required=True, help='排盘数据 JSON 文件')
    parser.add_argument('--reading', required=True, help='解读数据 JSON 文件')
    parser.add_argument('--template', help='HTML 模板路径（默认使用内置模板）')
    parser.add_argument('--output', required=True, help='输出 HTML 文件路径')

    args = parser.parse_args()

    with open(args.chart, 'r', encoding='utf-8') as f:
        chart_data = json.load(f)

    with open(args.reading, 'r', encoding='utf-8') as f:
        reading_data = json.load(f)

    template_path = args.template
    if not template_path:
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'chart_template.html')
        template_path = os.path.abspath(template_path)

    try:
        html = generate_html(chart_data, reading_data, template_path)
    except ReadingStructureError as exc:
        parser.error(str(exc))

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'命盘已生成: {args.output}')


if __name__ == '__main__':
    main()
