---
name: paper-intelligence
description: 按指定周期追踪 arXiv 与 HuggingFace 上的相关论文，围绕论文问题、方法、业务价值与局限逐篇解读，生成面向产品、研发与算法的 HTML 论文周报。用户要求生成论文周报或追踪某研究方向时使用；不负责竞品动态、GitHub 项目精选或知识点沉淀。
---

# 论文周报采集与分析

## 1. 职责定位

本 Skill 把“学术论文追踪”拆成两层，换业务线只动第一层：

- **检索对象层（换业务线只改这里）**：`assets/profiles/<对象>.json`。定义追踪谁——研究方向、关键词、arXiv 分类、相关性锚点、评分阈值、篇数上限、排除项。当前内置 `customer-service.json`（客服 Agent）。
- **编排层（换业务线不改）**：本 SKILL.md 的流程 + `scripts/` 的抓取/周期/渲染/校验 + `references/` 的文风与信源方法论。

要新增业务线，只需照 `customer-service.json` 的字段复制一份新 profile，编排层与脚本一字不改。

## 2. 触发条件

用户说“跑一下论文周报”“本周论文”“paper 周报跑一下”“追踪一下 XX 方向的论文”等。默认用客服 profile；用户指明其他业务线且存在对应 profile 时，换用该 profile。

**本 Skill 由人工手动触发，不配置 launchd / cron 等无人值守定时**。原因是核心步骤（逐篇四段式分析）由 Agent 亲自完成，本 Skill 明确禁止调用外部 LLM 接口（见步骤 3）；定时器只能拉起脚本，无法拉起“Agent 在场分析”，故全自动无人值守与本设计相斥。若确需无人值守，须先改变“分析由 Agent 自身产出”这一前提，届时四段式质量与归属红线将改由所调模型与脚本校验共同保证——这是另一种权衡，不在当前设计内。

## 3. 周期口径（固定，不得改成滚动 7 天）

- **建议运行节奏**：每周三由人工触发一次（非系统自动推送，见第 2 节）。
- **覆盖窗口**：上周三 00:00:00 至本周二 23:59:59。窗口结束日取最近一个已过完的周二；建议周三运行，此时恰好覆盖运行日往前推的完整 7 天。
- 窗口由 `scripts/resolve_week.py` 计算，不得手填日期。非周三运行也应使用最近一个完整窗口；当前脚本在周二会包含尚未结束的当天，见 [已知限制](references/self-test.md#3-已知限制)。遇到此情况须说明周期不完整，不按完整周报交付。

## 4. 输入与输出

- **输入**：一个 profile JSON（检索对象），一个由 `resolve_week.py` 算出的周期窗口。
- **输出**：一个 HTML 周报，含顶部结论（digest）与逐篇四段式卡片；每篇标题为可点击原文链接。

## 5. 执行流程

### 步骤 0：确认运行环境

- 使用 **Python 3.9 或更高版本**，并确保 `zoneinfo` 能读取 `Asia/Shanghai` 时区。周期计算、抓取和结构校验主要使用标准库。
- 渲染依赖 `jinja2`；抓取可选用 `certifi` 提供证书，未安装时使用系统证书。证书错误需排查，不能以关闭校验绕过。
- 首次运行、切换 Python 环境或报依赖错误时检查；同一环境已验证后，无需每轮重复检查。缺少 `jinja2` 时，在本次使用的环境中执行 `python3 -m pip install jinja2`；安装受限或失败时说明阻塞，不静默切换解释器或跳过渲染。

环境检查只确认能否运行，不能代替步骤 4 的内容校验和步骤 7 的交付检查。

### 步骤 1：锁定周期

```bash
python3 scripts/resolve_week.py
```

输出 `period_start` / `period_end`。测试可加 `--today YYYY-MM-DD` 覆盖当前日期。

### 步骤 2：抓取论文（无 LLM，纯数据）

```bash
python3 scripts/fetch_papers.py \
  --profile assets/profiles/customer-service.json \
  --start <period_start> --end <period_end> \
  --out /tmp/pi_fetched.jsonl
```

抓 arXiv RSS（按 profile 分类，本地关键词初筛）+ HuggingFace Daily Papers（逐日抓、按热度排序），按 `paper_id` 去重。

> 数据来源说明：HuggingFace Daily Papers 支持按历史日期逐天抓取，是周报的主力来源；arXiv RSS 是实时 feed，只含最近一两天新论文，周三实时跑时补窗口尾部，事后补跑历史窗口时可能返回 0，属正常现象，不影响周报完整性。

### 步骤 3：逐篇四段式分析（LLM——由 Agent／sub agent 自身完成）

> ⚠️ **禁止调用外部 LLM**：不使用 claude CLI、Claude API 或任何外部模型接口，所有分析由 Agent 或其 sub agent 直接完成输出。Python 侧只做抓取、渲染、校验。

1. 读 `/tmp/pi_fetched.jsonl`，按 profile 的 `research_directions` 与 `relevance_anchor` 粗筛出候选（技术领域不限，靠迁移价值判断）。
2. **逐篇**分析候选（论文多时可拆多个 sub agent，但每个 sub agent 一次只处理有限篇数，防止套模板兜底）。分析严格遵循 `references/analysis-style.md` 的四段式与归属红线：
   - `summary_zh`（论文要解决的问题）、`key_insight`（论文方法）、`actionable_idea`（论文方法的局限）三段写**论文本身**。
   - `inspiration`（对业务线的价值）是**唯一**允许出现业务线名称的段。
3. 每篇给 `relevance_score`（1–5），依据迁移价值强弱，非学术质量。低于 profile 的 `relevance_threshold` 不入选。
4. 补 `title_zh`（标题忠实意译）、`relevance_reason`（为何相关、迁移路径）。
5. 入选上限 = profile 的 `max_papers`（客服为 10），**相关性优先，不足不强凑**。
6. 整理为 JSONL（每行一篇），存 `/tmp/pi_analysis.jsonl`。字段：`paper_id / title / title_zh / authors / url / published_date / relevance_score / relevance_reason / summary_zh / key_insight / inspiration / actionable_idea`。

### 步骤 4：结构与红线校验（必须执行）

```bash
python3 scripts/validate_selection.py \
  --profile assets/profiles/customer-service.json \
  --analysis-file /tmp/pi_analysis.jsonl
```

校验四段字段齐全、入选不超上限、模板兜底文案、以及**归属红线**（痛点/方法/局限三段不得出现业务线名）。`passed=false` 时按 `errors` 修正，禁止带错渲染。

### 步骤 5：写顶部结论（digest）

按 `references/analysis-style.md` 第五节写一段 HTML：先给贯穿性判断（这批论文共同指向什么），再逐篇一句话点出其在逻辑链上的位置。存 `/tmp/pi_digest.html`。

### 步骤 6：渲染周报

```bash
python3 scripts/render_report.py \
  --profile assets/profiles/customer-service.json \
  --analysis-file /tmp/pi_analysis.jsonl \
  --digest-file /tmp/pi_digest.html \
  --period-start <period_start> --period-end <period_end> \
  --out /tmp/pi_weekly_<period_start>_<period_end>.html
```

渲染脚本按 profile 的阈值过滤、按分数排序、按上限截断。输出 `papers_count` 应等于入选篇数、不超上限。

### 步骤 7：交付前自检

- 用浏览器打开产物，确认标题可点击跳原文、四段式呈现正常、无空段。
- 确认 `papers_count` 合理（相关性筛选后的真实篇数，不是抓取总数）。

## 6. 入选原则

- 相关性优先，宁缺毋滥；上限内不强凑。
- 相关性靠迁移价值判断，技术领域不限；说不清迁移路径的不入选。
- 只呈现真实入选内容，不写“本周还检索到 N 篇不相关”这类负向流水，不写空栏目。
- 论文事实与对业务线的价值推断必须分开，不得让读者误以为论文在业务线场景验证过。

## 7. 单条四段式写法

详见 `references/analysis-style.md`。核心：痛点、方法、局限写论文（通用领域），业务线只进“价值”段；语言严肃、有逻辑、结论先行，不技术向也不大白话；每个效果数字标注指标口径与适用范围；不自造论文没有的名称与数据。

## 8. 自测场景

修改脚本、模板、依赖或切换 profile 后，按 [自测清单](references/self-test.md) 检查周期、筛选、归属、空周和渲染结果。清单区分预期行为与已知限制；仅写有自测说明，不代表已经执行或通过。

正常生成每期周报时，步骤 4 和步骤 7 仍须执行；不要求每期重复完整回归。
