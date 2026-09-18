"""
格局扫描与量化规则库
版本: v2.1（合并自社区共创版，含修正）

功能:
  1. reduce_empty_palaces  空宫借星安宫 + 能量降阶标记
  2. evaluate_gezhi        三方四正拓扑扫描、成格判定、三维行为量化
  3. track_time_mutagens   流年/大限化忌叠冲追踪（时空压力审计）

修正记录（相对社区版 v2.0）:
  - 【重要】SIHUA_JI_MAP 甲/乙/丙三项错用了化禄星（甲廉贞/乙天机/丙天同），
    已修正为标准生年四化忌星: 甲太阳 / 乙太阴 / 丙廉贞。
    该错误会导致甲/乙/丙流年（含 2024-2026）的压力审计整体错位。
  - 流年干支补齐地支计算（原版只算天干，地支硬编码"戌"有误；
    2024=甲辰 起算，2026=丙午）
  - 杀破狼判定扩展: 命宫本宫坐杀/破/贪，或三方四正（含空宫借星）会齐三星
  - 风险评级输出中文化
"""

# 1. 经典格局与行为学映射字典
GEZHI_PATTERN_MAP = {
    "ZIFU_WUXIANG": {
        "name": "紫府武相格",
        "tech_alias": "The Sovereign Platform (平台与资源整合型架构)",
        "description": "系统具备极强的抗周期防御能力与稳固的组织架构。先天禀赋偏向于在高度合规、有既定规则的大型系统内发挥管理与协同效能。其策略依赖于稳健运作和调动多方资源，而非破坏性开拓。"
    },
    "SHA_PO_LANG": {
        "name": "杀破狼格",
        "tech_alias": "The Dynamic Disruptor (高频波动与颠覆式开拓玩家)",
        "description": "人生范式由一系列不连续的脉冲和断裂式跃迁组成。具备极强的冷启动破局能力与高风险承受力，适合在多变、重博弈的动态环境中清洗旧产能、建立新系统。"
    },
    "JI_YUE_TONG_LIANG": {
        "name": "机月同梁格",
        "tech_alias": "稳定系统中的规划、协调与专业积累型",
        "description": "这个格局更像善于读懂规则、安排步骤并长期积累专业信用的人。古书所谓“作吏人”，放到现代不必只理解为公务员，也可延伸为制度清楚、讲专业分工、需要耐心协调的组织与岗位。",
        "plain_summary": "四颗星各有分工：天机偏规划与应变，太阴偏细节、资源与审美，天同偏协调与服务，天梁偏原则、审核与照顾。组合起来的优势通常不是冒险抢跑，而是把复杂事情整理成可执行方案。",
        "strengths": "分析梳理、写作策划、流程优化、跨部门协调、风险控制、专业服务与持续学习。",
        "modern_roles": "咨询与运营、教育培训、研究与数据、项目或产品管理、医疗健康支持、合规审查、公共服务，以及需要规划能力的设计类工作。",
        "pitfalls": "容易想得多、决定得慢，或因求稳而错过窗口；也可能擅长给方案，却把真正行动一再延后。适合给判断设期限，并用小步试错代替长期空想。",
        "formation_note": "本报告采用“三方四正会齐机、月、同、梁至少三曜”的宽口径识别。格局表示背景倾向，不等同身份高低、职业保证或人生定论。"
    },
    "YANG_LIANG_CHANG_LU": {
        "name": "阳梁昌禄格",
        "tech_alias": "The Licensed Specialist (强壁垒型专业技术精英)",
        "description": "日照雷门，皇榜夺魁。这类系统极度依赖个人信用（IP）与极高的行业技术/政策牌照壁垒来进行安全防御。在需要强烈资质认可、法律或技术权威背书的领域，能发挥出最大概率的阶层跃迁潜能。"
    },
    "JU_RI_TONG_GONG": {
        "name": "巨日同宫格",
        "tech_alias": "The Cross-Border Communicator (跨境传播与心智带宽架构)",
        "description": "巨日同宫，名振文化。具备极强的跨文化、跨地域信息传播能力与内容输出带宽，最适合打破信息不对称，进行大规模的思想、语言或异地技术标准传播。"
    },
    "FUXI_CHAO_YUAN": {
        "name": "府相朝垣格",
        "tech_alias": "The Distributed Redundancy Architecture (分布式容灾与高级协同架构)",
        "description": "天府天相联立朝拱，一生多得朋辈与行业生态的强力辅佐。系统本身极具稳健性与容灾复原能力，属于极其优秀的高级合伙人或联席架构。"
    },
    "MATOU_DAIJIAN": {
        "name": "马头带剑格",
        "tech_alias": "The Extreme Stress Breakthrough (逆境突围者 / 兵团司令型变体)",
        "description": "午宫擎羊坐命的极端压力变体。主在极度混乱、高压、甚至恶劣的外部系统环境中，能够完成高风险、高回报的强力破局，属于乱世出英豪的典型脉冲架构。"
    },
    "ZA_GE": {
        "name": "泛用型自适应配置 (杂格)",
        "tech_alias": "The General Adaptor (高自适应环境韧性盘)",
        "description": "未命中经典极端极性成格。系统本身不具备特定的偏激缺陷或优势，代表其受大限环境和主观行动的塑造弹性极大。具备极高的自适应环境调校能力。"
    }
}

# 2. 三方四正坐标映射（12地支环形链表索引）
ZODIAC_INDEX = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
STEM_CYCLE = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 煞星常量
SHA_STARS = ["擎羊", "陀罗", "火星", "铃星", "地空", "地劫"]

# 标准生年四化 · 化忌星对照表（天干 → 忌星）
# 甲太阳 乙太阴 丙廉贞 丁巨门 戊天机 己文曲 庚天同 辛文昌 壬武曲 癸贪狼
SIHUA_JI_MAP = {
    "甲": "太阳", "乙": "太阴", "丙": "廉贞", "丁": "巨门", "戊": "天机",
    "己": "文曲", "庚": "天同", "辛": "文昌", "壬": "武曲", "癸": "贪狼"
}


def get_year_ganzhi(year):
    """返回目标公历年的干支（如 2026 → ('丙', '午')）。以 2024 甲辰年为基准。"""
    stem = STEM_CYCLE[(year - 2024) % 10]
    chen_idx = ZODIAC_INDEX.index("辰")  # 2024 = 甲辰
    branch = ZODIAC_INDEX[(chen_idx + (year - 2024)) % 12]
    return stem, branch


def get_sanfang_sizheng_indices(current_branch):
    """根据当前宫位地支，计算三方四正的其它三个地支"""
    curr_idx = ZODIAC_INDEX.index(current_branch)
    opposite_idx = (curr_idx + 6) % 12          # 对宫 (迁移位)
    sanhe_1_idx = (curr_idx + 4) % 12           # 三合左翼 (财帛/官禄位)
    sanhe_2_idx = (curr_idx + 8) % 12           # 三合右翼 (官禄/财帛位)

    return {
        "ben_gong": ZODIAC_INDEX[curr_idx],
        "dui_gong": ZODIAC_INDEX[opposite_idx],
        "sanhe_1": ZODIAC_INDEX[sanhe_1_idx],
        "sanhe_2": ZODIAC_INDEX[sanhe_2_idx]
    }


def get_sanfang_sizheng(chart_data, palace_name="命宫"):
    """从排盘数据中提取指定宫位三方四正的所有星曜"""
    target_palace = next((p for p in chart_data["palaces"] if p["name"] == palace_name), None)
    if not target_palace:
        return {"major_stars": [], "minor_stars": [], "adjective_stars": []}

    sfsz_branches = get_sanfang_sizheng_indices(target_palace["earthly_branch"])

    result = {"major_stars": [], "minor_stars": [], "adjective_stars": []}
    for palace in chart_data["palaces"]:
        if palace["earthly_branch"] in sfsz_branches.values():
            result["major_stars"].extend(palace.get("major_stars", []))
            result["minor_stars"].extend(palace.get("minor_stars", []))
            result["adjective_stars"].extend(palace.get("adjective_stars", []))
    return result


def count_shaxing(star_set):
    """统计煞星数量（接受字典或列表）"""
    if isinstance(star_set, dict):
        all_stars = star_set.get("major_stars", []) + star_set.get("minor_stars", []) + star_set.get("adjective_stars", [])
    else:
        all_stars = list(star_set)
    return sum(1 for star in all_stars if star in SHA_STARS)


def evaluate_gezhi(chart_json):
    """
    输入: 由 iztro-py 生成的标准命盘 json（经 reduce_empty_palaces 处理后更佳）
    输出: 格局判定、三维行为学量化指标、系统压力预警
    """
    # 3.1 定位命宫所在的地支
    ming_palace = next(p for p in chart_json["palaces"] if "命宫" in p["tags"])
    ming_branch = ming_palace["earthly_branch"]

    # 3.2 拉取三方四正的所有宫位星曜拓扑集合
    sfsz_map = get_sanfang_sizheng_indices(ming_branch)
    sfsz_palaces = [p for p in chart_json["palaces"] if p["earthly_branch"] in sfsz_map.values()]

    # 聚合三方四正所有的主星与煞星（空宫优先取借星）
    all_major_stars = []
    all_minor_stars = []
    shaxing_count = 0
    has_huoxing, has_lingxing, has_qingyang, has_jumen = False, False, False, False

    for p in sfsz_palaces:
        all_major_stars.extend(p.get("borrowed_major_stars", []) or p["major_stars"])
        all_minor_stars.extend(p.get("borrowed_minor_stars", []) or p["minor_stars"])

        for star in SHA_STARS:
            if star in p["minor_stars"] or star in p.get("adjective_stars", []):
                shaxing_count += 1
                if star == "火星": has_huoxing = True
                if star == "铃星": has_lingxing = True
                if star == "擎羊": has_qingyang = True
        if "巨门" in p["major_stars"]:
            has_jumen = True

    # 3.3 初始化量化矩阵维度 (3核心维度，5级量化)
    risk_tolerance = 3
    fluctuation_resilience = 3
    decision_aggressiveness = 3
    pattern_key = "ZA_GE"  # 默认杂格

    # 3.4 严格数理判定矩阵
    # (A) 杀破狼格判定: 命宫本宫坐杀/破/贪，或三方四正（含借星）会齐三星
    sha_po_lang_stars = {"七杀", "破军", "贪狼"}
    in_ming = sha_po_lang_stars & set(ming_palace["major_stars"])
    sfsz_complete = sha_po_lang_stars.issubset(set(all_major_stars))
    if in_ming or sfsz_complete:
        pattern_key = "SHA_PO_LANG"
        risk_tolerance = 5
        decision_aggressiveness = 5
        # 突发变体：火贪/铃贪格加权（已由 5 封顶，保留标记位）

    # (B) 紫府武相格判定
    elif sum(1 for s in ["紫微", "天府", "武曲", "天相"] if s in all_major_stars) >= 2 and shaxing_count <= 2:
        pattern_key = "ZIFU_WUXIANG"
        risk_tolerance = 2
        decision_aggressiveness = 2
        fluctuation_resilience = 5

    # (C) 机月同梁格判定
    elif sum(1 for s in ["天机", "太阴", "天同", "天梁"] if s in all_major_stars) >= 3:
        pattern_key = "JI_YUE_TONG_LIANG"
        risk_tolerance = 2
        decision_aggressiveness = 1
        fluctuation_resilience = 3

    # (D) 阳梁昌禄格判定（含空宫降阶逻辑）
    # TODO: 传统成格需会禄存/化禄，当前仅查太阳+天梁+文昌，纯度判定偏宽
    elif "太阳" in all_major_stars and "天梁" in all_major_stars and "文昌" in all_minor_stars:
        if ming_palace.get("is_empty_palace", False):
            if "巨门" in all_major_stars:
                pattern_key = "JU_RI_TONG_GONG"   # 降阶为巨日变体
                risk_tolerance = 4
                decision_aggressiveness = 4
                fluctuation_resilience = 3
            else:
                pattern_key = "ZA_GE"              # 降阶为泛用型
        else:
            pattern_key = "YANG_LIANG_CHANG_LU"
            risk_tolerance = 3
            decision_aggressiveness = 3
            fluctuation_resilience = 4

    # (E) 巨日同宫格判定
    elif "巨门" in ming_palace["major_stars"] and "太阳" in ming_palace["major_stars"] and ming_branch in ["寅", "申"]:
        pattern_key = "JU_RI_TONG_GONG"
        risk_tolerance = 4
        decision_aggressiveness = 4
        fluctuation_resilience = 3

    # (F) 马头带剑格（特殊变体）
    elif ming_branch == "午" and "擎羊" in ming_palace.get("minor_stars", []) and sum(1 for s in ["贪狼", "天同", "天梁"] if s in ming_palace["major_stars"]) >= 1:
        pattern_key = "MATOU_DAIJIAN"
        risk_tolerance = 5
        decision_aggressiveness = 5
        fluctuation_resilience = 4

    # 3.5 煞星对多维指标的动态修正（数理降阶逻辑）
    if shaxing_count >= 4:
        risk_tolerance = min(5, risk_tolerance + 1)
        fluctuation_resilience = max(1, fluctuation_resilience - 2)

    # 3.6 系统压力测试扫描
    stress_warnings = []
    if has_jumen and (has_huoxing or has_lingxing) and has_qingyang:
        stress_warnings.append({
            "code": "COMM_OVERLOAD",
            "type": "巨火羊/巨铃羊 (Communication Overload)",
            "desc": "压力预警：面临高压环境时极易因情绪化触发纠纷、口舌撕裂，或心理防御机制过载。"
        })

    # 3.7 打包输出结果
    pattern_meta = GEZHI_PATTERN_MAP[pattern_key]
    return {
        "gezhi_name": pattern_meta["name"],
        "tech_alias": pattern_meta["tech_alias"],
        "description": pattern_meta["description"],
        "plain_summary": pattern_meta.get("plain_summary", ""),
        "strengths": pattern_meta.get("strengths", ""),
        "modern_roles": pattern_meta.get("modern_roles", ""),
        "pitfalls": pattern_meta.get("pitfalls", ""),
        "formation_note": pattern_meta.get("formation_note", ""),
        "quant_metrics": {
            "risk_tolerance": risk_tolerance,                  # 系统风险耐受度 (1-5)
            "fluctuation_resilience": fluctuation_resilience,   # 逆境波动恢复力 (1-5)
            "decision_aggressiveness": decision_aggressiveness  # 决策激进度 (1-5)
        },
        "stress_warnings": stress_warnings
    }


def reduce_empty_palaces(chart_json):
    """
    输入: 原始包含空宫的 chart_json
    输出: 完成借星安宫、标记能量降阶系数的数据矩阵
    """
    palaces = chart_json["palaces"]

    for p in palaces:
        # 检测是否为主星空宫
        if not p.get("major_stars") or len(p["major_stars"]) == 0:
            curr_idx = ZODIAC_INDEX.index(p["earthly_branch"])
            opposite_branch = ZODIAC_INDEX[(curr_idx + 6) % 12]
            opposite_palace = next(op for op in palaces if op["earthly_branch"] == opposite_branch)

            # 1. 实施借星安宫 (镜像克隆对宫主星、辅星)
            p["borrowed_major_stars"] = opposite_palace.get("major_stars", []).copy()
            p["borrowed_minor_stars"] = opposite_palace.get("minor_stars", []).copy()

            # 2. 注入元数据标记
            p["is_empty_palace"] = True
            p["borrowed_from_branch"] = opposite_branch

            # 3. 能量衰减系数（先天底色打七折）
            p["energy_coefficient"] = 0.7

            # 4. 边界压力红线检测：对宫见煞，空宫无防御，风险加倍
            opposite_shaxing = [s for s in SHA_STARS
                                if s in opposite_palace.get("minor_stars", [])]
            if opposite_shaxing:
                p["system_vulnerability"] = "High (对宫煞星直冲，空宫防线坍塌)"
                p["energy_coefficient"] = 0.5
            else:
                p["system_vulnerability"] = "Medium-Flexible (空宫弹性承接)"
        else:
            p["is_empty_palace"] = False
            p["energy_coefficient"] = 1.0
            p["system_vulnerability"] = "Stable"

    return chart_json


def track_time_mutagens(chart_json, current_year=2026):
    """
    输入: 包含基础排盘与格局信息的 chart_json（solar_date / birth_year 至少一项）+ 目标流年年份
    输出: 生年、大限、流年化忌的交冲坐标与各宫时空压力评分
    """
    palaces = chart_json["palaces"]

    # 1. 提取先天的生年化忌宫位
    birth_ji_branch = None
    if chart_json.get("year_mutagens"):
        for m in chart_json["year_mutagens"]:
            if m.get("mutagen") == "化忌":
                birth_ji_branch = m.get("branch")

    # 2. 定位当前大限宫位与化忌（中州派: 大限宫干飞四化）
    birth_year = chart_json.get("birth_year")
    if not birth_year and chart_json.get("solar_date"):
        birth_year = int(str(chart_json["solar_date"]).split("-")[0])
    if not birth_year:
        raise ValueError("chart_json 缺少 birth_year / solar_date，无法计算虚岁定位大限")
    current_age = current_year - birth_year + 1  # 虚岁

    daxian_palace = None
    for p in palaces:
        if p.get("decadal_range"):
            try:
                start_age, end_age = map(int, p["decadal_range"].split("-"))
                if start_age <= current_age <= end_age:
                    daxian_palace = p
                    break
            except (ValueError, AttributeError):
                continue

    daxian_ji_star = SIHUA_JI_MAP.get(daxian_palace["heavenly_stem"]) if daxian_palace else None

    # 3. 目标流年天干地支与流年化忌
    liunian_stem, liunian_branch = get_year_ganzhi(current_year)
    liunian_ji_star = SIHUA_JI_MAP.get(liunian_stem)

    # 4. 遍历十二宫，计算每一宫的时空叠忌权重（压力测试指数）
    time_analysis_report = []

    for p in palaces:
        branch = p["earthly_branch"]
        ji_count = 0.0
        ji_sources = []

        # 生年化忌是否落入本宫或直冲对宫
        curr_idx = ZODIAC_INDEX.index(branch)
        opposite_branch = ZODIAC_INDEX[(curr_idx + 6) % 12]

        if branch == birth_ji_branch:
            ji_count += 1
            ji_sources.append("生年化忌本宫坐守")
        if opposite_branch == birth_ji_branch:
            ji_count += 1.5  # 对宫冲射危害更大
            ji_sources.append("生年化忌对宫直冲")

        # 大限/流年化忌星曜是否在本宫（含借星）
        all_my_stars = (
            p.get("major_stars", []) +
            p.get("borrowed_major_stars", []) +
            p.get("minor_stars", []) +
            p.get("borrowed_minor_stars", [])
        )

        if daxian_ji_star and daxian_ji_star in all_my_stars:
            ji_count += 1
            ji_sources.append(f"大限化忌 [{daxian_ji_star}] 激活")

        if liunian_ji_star and liunian_ji_star in all_my_stars:
            ji_count += 1
            ji_sources.append(f"{current_year}流年化忌 [{liunian_ji_star}] 引入")

        # 5. 划定时空压力评级（中文）
        if ji_count >= 2.5:
            risk_level = "高危 · 极端系统性震荡，建议低能耗静养"
            is_hotspot = True
        elif ji_count >= 1.0:
            risk_level = "预警 · 局部压力过载，注意对冲风险"
            is_hotspot = False
        else:
            risk_level = "平稳 · 安全运行期"
            is_hotspot = False

        if ji_count > 0:
            time_analysis_report.append({
                "palace_name": p["name"],
                "earthly_branch": branch,
                "stress_score": round(ji_count, 2),
                "risk_level": risk_level,
                "trigger_sources": ji_sources,
                "is_hotspot": is_hotspot
            })

    # 按压力分降序排列
    time_analysis_report.sort(key=lambda x: x["stress_score"], reverse=True)

    return {
        "target_year": current_year,
        "liunian_stem": liunian_stem,
        "liunian_branch": liunian_branch,
        "liunian_ji_star": liunian_ji_star,
        "daxian_ji_star": daxian_ji_star,
        "current_decadal_palace": daxian_palace["name"] if daxian_palace else None,
        "birth_year_ji_branch": birth_ji_branch,
        "stress_hotspots": [r for r in time_analysis_report if r["is_hotspot"]],
        "full_time_log": time_analysis_report
    }


if __name__ == "__main__":
    import json

    # 用真实排盘数据做冒烟测试（配合 calculate_chart.py 的输出）
    import subprocess
    try:
        result = subprocess.run(
            ["python3", __file__.replace("gezhi_rules.py", "calculate_chart.py"),
             "--solar", "1991-8-15", "--hour", "1", "--gender", "男"],
            capture_output=True, text=True
        )
        chart = json.loads(result.stdout)
        reduce_empty_palaces(chart)
        print("=== 格局扫描 ===")
        print(json.dumps(evaluate_gezhi(chart), ensure_ascii=False, indent=2))
        print("\n=== 流年干支自检 ===")
        for y in [2024, 2025, 2026, 2027]:
            print(y, "".join(get_year_ganzhi(y)))
        print("\n=== 时空压力审计 ===")
        print(json.dumps(track_time_mutagens(chart, current_year=2026)["stress_hotspots"],
                         ensure_ascii=False, indent=2))
    except FileNotFoundError:
        print("冒烟测试需要 calculate_chart.py 在同目录")
