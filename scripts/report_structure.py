"""V2 生活报告的数据契约、兼容识别与校验。"""

from copy import deepcopy


CHAPTER_ORDER = (
    "personality",
    "career",
    "wealth",
    "relationship",
    "wellbeing",
    "network",
    "cycles",
    "family",
    "work_mode",
    "lifestyle",
)

CHAPTER_FIELDS = (
    "verdict",
    "manifestations",
    "strengths",
    "pitfalls",
    "actions",
    "evidence",
)


class ReadingStructureError(ValueError):
    """解读数据不满足 V2 完整版契约。"""


def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set)):
        return not value or all(_is_blank(item) for item in value)
    if isinstance(value, dict):
        return not value or all(_is_blank(item) for item in value.values())
    return False


def normalize_reading(reading):
    """识别 V2 或旧版 cards；返回副本，避免渲染过程污染调用方。"""
    normalized = deepcopy(reading or {})
    if "chapters" in normalized or normalized.get("format_version") == 2:
        normalized["format"] = "v2"
    else:
        normalized["format"] = "legacy"
    return normalized


def validate_v2_reading(reading):
    """返回所有结构问题；不补写或猜测任何命理解读。"""
    errors = []
    if not isinstance(reading, dict):
        return ["reading 必须是 JSON 对象"]

    overview = reading.get("overview")
    if not isinstance(overview, dict):
        errors.append("overview 缺失或不是对象")
    else:
        items = overview.get("items")
        if not isinstance(items, list) or not 4 <= len(items) <= 6:
            errors.append("overview.items 必须包含 4–6 条摘要")
        elif any(_is_blank(item) for item in items):
            errors.append("overview.items 不能包含空白项")

    chapters = reading.get("chapters")
    if not isinstance(chapters, dict):
        errors.append("chapters 缺失或不是对象")
        return errors

    for key in CHAPTER_ORDER:
        chapter = chapters.get(key)
        if not isinstance(chapter, dict):
            errors.append(f"缺少章节：{key}")
            continue
        for field in CHAPTER_FIELDS:
            if _is_blank(chapter.get(field)):
                errors.append(f"缺少或留空：{key}.{field}")

    return errors


def require_valid_v2_reading(reading):
    """校验失败时抛出包含所有问题的可读异常。"""
    errors = validate_v2_reading(reading)
    if errors:
        raise ReadingStructureError("V2 解读结构不完整：\n- " + "\n- ".join(errors))
    return reading
