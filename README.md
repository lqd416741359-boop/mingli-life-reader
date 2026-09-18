# 命理解读师·生活版

一个面向普通读者的紫微斗数＋四柱八字综合报告 Skill。输入出生日期、时辰与性别后，可生成高对比度宣纸风 HTML 命盘，并由 Agent 进一步导出 PDF。

本项目基于 [learnwithu/mingli-master](https://github.com/learnwithu/mingli-master) 二次开发。原项目采用 MIT License；本仓库保留原版权声明、许可证与第三方说明。

> 本项目用于传统文化阅读与自我反思，不是科学预测、医疗诊断、投资建议或人生决定工具。

## 主要内容

- 紫微斗数十二宫、星曜、四化、大限、空宫借星、格局与流年压力观察。
- 四柱八字、生肖、出生年干支、年柱纳音、日主五行、十神、藏干、地势与空亡。
- 月令十神命格入门标签，以及食神、伤官、印星、财官比劫等白话性格说明。
- 显性五行数量、八组大运、逐年流年与小运、常用神煞。
- 性格天赋、事业学业、稳定任职／副业／创业、财运、婚恋、父母子女、人际贵人与生活方式。
- 袁天罡称骨歌民俗附录，并提供现代白话解释。
- 可选三世书条目式附录：前世今生未来、夫妻婚姻、子女、六亲兄弟、生肖、骨格学堂手艺、财富与佛缘。
- 三世书安全改写器：过滤寿命死法、疾病诊断、克亲断言和付费消灾内容。
- 单一高对比度淡黄色宣纸主题，适合浏览与打印。

## 安装

将 GitHub 仓库地址交给支持 Agent Skills 的 AI，并告诉它安装这个 Skill；也可以手动复制到 Skills 目录，例如：

```text
~/.codex/skills/mingli-life-reader/
```

安装依赖：

```bash
python -m pip install "iztro-py>=0.5.0" "lunar_python>=1.4.0"
```

## 使用方法

安装后可以直接对 Agent 说：

```text
请用命理解读师·生活版帮我排盘：
公历 2001 年 3 月 14 日，午时，女。
重点分析性格、事业、财运、婚恋和未来三年的生活节奏，并生成 HTML 报告。
```

生成确定性基础盘：

```bash
python scripts/calculate_chart.py \
  --solar 2001-03-14 \
  --hour 6 \
  --gender 女 \
  --year 2026 \
  --output chart.json
```

农历输入示例：

```bash
python scripts/calculate_chart.py \
  --lunar 2001-02-20 \
  --hour 6 \
  --gender 女 \
  --year 2026 \
  --output chart.json
```

准备符合 [SKILL.md](SKILL.md) 结构的 `reading.json` 后生成 HTML：

```bash
python scripts/generate_html.py --chart chart.json --reading reading.json --output report.html
```

### 时辰索引

| 索引 | 时辰 | 索引 | 时辰 |
|---:|---|---:|---|
| 0 | 早子 | 7 | 未 |
| 1 | 丑 | 8 | 申 |
| 2 | 寅 | 9 | 酉 |
| 3 | 卯 | 10 | 戌 |
| 4 | 辰 | 11 | 亥 |
| 5 | 巳 | 12 | 晚子 |
| 6 | 午 |  |  |

## 完整版报告

默认可覆盖基础命盘、生肖纳音、日主与命格、性格天赋、事业学业、任职／副业／创业、财运、婚恋、父母子女、当前大运、贵人、身心生活方式、人生总结和生活指南。用户主动提出时，可增加称骨歌、三世书和手相文化观察。

仓库内置 HTML 生成器。PDF 导出由运行 Skill 的 Agent 根据环境完成，推荐使用浏览器打印或 ReportLab，并在交付前逐页检查中文字体、分页和表格。

## 安全边界

- 不预测寿命、死亡方式、具体疾病或灾祸。
- 不断言胎儿性别、准确子女数量、唯一正缘年份或具体财富金额。
- 不使用“克父母、克子女”等伤害性表达。
- 不推荐纸钱、香烛、法事或其他付费消灾方案。
- 健康、生育、投资、法律和重大人生决策应回到现实证据与专业意见。
- 三世书的前世、今生、未来是民俗寓言，不是可验证事实。

## 项目结构

```text
mingli-life-reader/
├─ SKILL.md
├─ scripts/                 排盘、八字扩展、HTML 生成与安全过滤
├─ references/              星曜、四化、八字、完整版报告与三世书规范
├─ templates/               宣纸风 HTML 模板
├─ tests/                   安全过滤测试
├─ LICENSE
└─ THIRD_PARTY_NOTICES.md
```

## 隐私

出生资料属于敏感个人信息。不要把真实命盘输入、生成的 `chart.json`、`reading.json`、HTML、PDF、照片或校准回答提交到公开仓库。建议在个人工作目录保存输入与输出，并在提交前检查 Git diff。

## 致谢与许可证

- 原项目：[learnwithu/mingli-master](https://github.com/learnwithu/mingli-master)
- 四柱历法计算：[6tail/lunar-python](https://github.com/6tail/lunar-python)
- 紫微斗数排盘：[iztro-py](https://pypi.org/project/iztro-py/)

项目采用 MIT License。发布和分发修改版时，请保留 [LICENSE](LICENSE) 与 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
