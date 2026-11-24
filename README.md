# Paper Intelligence

本仓库是一份可被 Agent 加载的 Skill：在给定业务方向下，抓取 arXiv 与 HuggingFace 在覆盖窗口内的相关论文，逐篇完成四段式解读，并渲染为本地 HTML 周报。默认检索对象为**客服 Agent**。

目标读者为**产品、研发与算法**。产品侧关注可迁移价值与决策线索；研发侧关注方法边界与工程前置条件；算法侧关注问题建模与评测口径。

**维护者**：[HalaMarkPang](https://github.com/HalaMarkPang)（群）  
**License**：MIT

## 1. 产出物

输出为一份本地 HTML 周报，结构固定：

| 组成部分 | 说明 |
|----------|------|
| 顶部结论（digest） | 对本批论文的贯穿性判断，并标明每篇在该判断逻辑链上的位置 |
| 逐篇卡片 | 英文原标题（可点击跳转原文）、中文意译标题、相关性评分（1–5）、四段式解读 |
| 覆盖窗口 | 滚动近 7 天：以 Asia/Shanghai 的「昨天」为结束日，往前共 7 个完整自然日；运行当天不计入 |
| 入选上限 | 默认至多 10 篇；按相关性优先筛选，不足额不补 |

四段式字段与归属如下。论文事实与业务推断必须分开表述，避免读者误以为论文已在业务场景中验证。

| 字段 | 归属 | 写什么 |
|------|------|--------|
| 论文要解决的问题 | 论文本身 | 通用领域面临的问题及其难点 |
| 论文方法 | 论文本身 | 解决思路 / 机制，及关键结果（须标注指标口径与适用范围） |
| 对业务线的价值 | 业务线 | 方法或结论迁移到该业务线可解决的实际问题；**唯一允许出现业务线名称的段落** |
| 论文方法的局限 | 论文本身 | 方法边界、未解决问题、迁移前须验证的前提 |

相关性判定不以技术领域划界，而以「方法、结论或问题建模能否迁移到业务实际问题」为准。说不清迁移路径的论文不入选。

换业务线时，复制 `assets/profiles/customer-service.json` 并调整关键词与相关性锚点即可；编排层与脚本无需修改。完整执行流程见 [`SKILL.md`](SKILL.md)。

## 2. 安装与运行

**运行前提**：Python 3.9 或更高版本；本机可访问 HuggingFace Daily Papers 与 arXiv；具备可加载 Agent Skill 的客户端（如 Claude Code、Cursor、Codex）。

```bash
git clone https://github.com/HalaMarkPang/paper-intelligence.git
cd paper-intelligence
bash install.sh
```

`install.sh` 会校验 Python 版本、安装 `jinja2`，并将 Skill 导出至 `~/.agent-skills/paper-intelligence`。若检测到 Claude Code，会额外软链至 `~/.claude/skills/paper-intelligence`。

环境自检：

```bash
python3 scripts/resolve_week.py
```

正常输出应包含 `period_start`、`period_end`，且 `mode` 为 `rolling_7d`。

安装完成后，在 Agent 会话中以自然语言触发即可，例如：

- 「生成论文周报」「本周论文周报」
- 「按某历史日期补跑论文周报」（脚本以 `--today` 覆盖运行日，窗口仍按滚动 7 天计算）
- 「追踪 XX 方向的论文」（须已存在对应 profile）

触发后，Agent 依次执行：锁定周期 → 抓取 → 逐篇分析 → 红线校验 → 渲染 HTML。Python 侧仅负责抓取、渲染与结构校验；**禁止**调用外部大模型 API，分析由当前会话中的 Agent 直接完成。

## 3. 适用对象与阅读方式

| 角色 | 建议阅读重点 |
|------|----------------|
| 产品 | 顶部结论与「对业务线的价值」段，用于判断是否值得立项或试点 |
| 研发 | 「论文方法」与「局限」段，用于评估工程前置条件与失败模式 |
| 算法 | 问题建模、评测口径与 `relevance_reason`，用于对齐研究方向 |

## 4. 边界与限制

1. **须人工触发**。四段式分析依赖 Agent 在会话中产出，不支持 launchd / cron 等无人值守定时。
2. **覆盖窗口为滚动近 7 天**，不以固定「周几至周几」对齐；不同运行日得到的窗口随日期滚动。
3. **双信源特性不同**。HuggingFace Daily Papers 支持按历史日期逐日抓取，为周报主力来源；arXiv RSS 为实时 feed，通常仅含近一两天新论文。补跑较早窗口时，arXiv 侧可能返回 0 篇，属预期行为，不单独构成周报缺失。
4. **产出仅落盘为本地 HTML**，不自动分发至文档系统或即时通讯渠道。
5. **分析质量取决于所用模型**。不同模型在解读深度与事实准确度上存在差异；交付前须按 [`SKILL.md`](SKILL.md) 完成结构校验与页面自检。

## 5. 依赖

见 [`requirements.txt`](requirements.txt)。运行必备第三方库仅为 `jinja2`；`certifi` 可选，用于 HTTPS 证书校验，缺失时回退系统证书。其余脚本使用 Python 标准库。
