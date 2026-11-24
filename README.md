# Paper Intelligence

Paper Intelligence 是用于追踪学术论文并生成周报的 Agent Skill。它在指定业务方向下抓取 arXiv 与 HuggingFace 在覆盖窗口内的论文，按迁移价值筛选，逐篇完成四段式解读，并渲染为本地 HTML 周报。默认检索对象为客服 Agent，适用于 Claude Code、Codex、Cursor 等支持 Skill 的 Agent 客户端。

目标读者为产品、研发与算法人员：产品侧关注可迁移价值与决策线索，研发侧关注方法边界与工程前置条件，算法侧关注问题建模与评测口径。

## 解决的问题

未经约束的论文追踪，常见缺陷包括：

1. 按技术领域或热度筛选，无法说明论文与业务问题的关联，入选结果难以支撑决策。
2. 论文自身结论与业务推断混写，读者误以为方法已在业务场景中验证。
3. 引用效果数字时缺少指标口径与适用范围，结论被放大。
4. 为满足篇数纳入关联薄弱的论文，或以模板化表述填充解读。
5. 覆盖周期由人工填写，各期范围不一致，无法比较。

## 工作机制

| 问题 | 机制 | 规则文件 |
|---|---|---|
| 关联无法说明 | 相关性以“方法、结论或问题建模能否迁移到业务问题”判定，不以技术领域划界；评分 1–5，低于阈值不入选；无法说明迁移路径的不入选 | [source-rules.md](references/source-rules.md) |
| 事实与推断混写 | 四段式归属规则：问题、方法、局限三段只写论文本身；业务线名称仅允许出现在“对业务线的价值”一段，由脚本校验 | [analysis-style.md](references/analysis-style.md)、[validate_selection.py](scripts/validate_selection.py) |
| 数字脱离口径 | 每个效果数字须标注指标口径与适用范围；不引入论文未给出的名称与数据 | [analysis-style.md](references/analysis-style.md) |
| 凑数与套话 | 入选上限默认 10 篇，相关性优先，不足额不补；脚本校验篇数上限与模板化兜底文案 | [source-rules.md](references/source-rules.md)、[validate_selection.py](scripts/validate_selection.py) |
| 周期不一致 | 覆盖窗口由脚本计算，不手填日期；补跑以 `--today` 覆盖运行日 | [resolve_week.py](scripts/resolve_week.py) |

检索对象与编排流程相互分离。研究方向、关键词、arXiv 分类、相关性锚点、评分阈值、篇数上限与排除项均定义于 `assets/profiles/<对象>.json`；更换业务线时仅新增 profile，编排流程与脚本无需修改。

## 工作流程

```text
锁定覆盖窗口（resolve_week.py）
→ 抓取 arXiv RSS 与 HuggingFace Daily Papers 并去重（fetch_papers.py）
→ Agent 逐篇筛选、评分并完成四段式解读
→ 结构与归属规则校验（validate_selection.py）
→ Agent 撰写顶部结论
→ 渲染 HTML 周报（render_report.py）
→ 交付前页面自检
```

Python 脚本仅负责周期计算、抓取、校验与渲染；筛选与解读由当前会话中的 Agent 完成。完整步骤见 [SKILL.md](SKILL.md)。

## 约束与边界

1. **人工触发**：四段式解读须由 Agent 在会话中完成，不支持 launchd、cron 等无人值守定时运行。
2. **不调用外部模型接口**：脚本不调用任何外部大模型 API；分析由当前会话中的 Agent 或其子 Agent 完成。
3. **滚动窗口**：覆盖窗口以 Asia/Shanghai 时区的前一日为结束日，向前共 7 个完整自然日，运行当日不计入；窗口随运行日期滚动，不按固定星期对齐。
4. **信源覆盖差异**：HuggingFace Daily Papers 支持按历史日期逐日抓取，为主要来源；arXiv RSS 为实时 feed，通常仅含最近一至两天的论文。补跑较早窗口时 arXiv 侧返回 0 篇属预期行为，不构成周报缺失。
5. **校验不通过不渲染**：结构或归属校验未通过时，须按错误项修正后方可渲染。
6. **仅本地交付**：产出为本地 HTML 文件，不自动分发至文档系统或即时通讯渠道。
7. **质量依赖模型**：解读深度与事实准确度取决于所用模型；交付前须完成结构校验与页面自检。

## 安装

运行前提：Python 3.9 或更高版本；本机可访问 HuggingFace Daily Papers 与 arXiv；具备可加载 Agent Skill 的客户端。

```bash
git clone https://github.com/HalaMarkPang/paper-intelligence.git
cd paper-intelligence
bash install.sh
```

`install.sh` 校验 Python 版本、安装 `jinja2`，并将 Skill 导出至 `~/.agent-skills/paper-intelligence`；检测到 Claude Code 时，另行软链至 `~/.claude/skills/paper-intelligence`。Cursor 等客户端可直接引用仓库目录或导出目录。

环境自检：

```bash
python3 scripts/resolve_week.py
```

输出应包含 `period_start` 与 `period_end`，且 `mode` 为 `rolling_7d`。

依赖见 [requirements.txt](requirements.txt)。必需的第三方库仅为 `jinja2`；`certifi` 为可选项，用于 HTTPS 证书校验，未安装时使用系统证书。其余脚本仅使用 Python 标准库。

## 使用

在 Agent 会话中以自然语言触发：

| 场景 | 示例 |
|---|---|
| 生成当期周报 | 生成论文周报 |
| 补跑历史窗口 | 以 2026-11-01 为运行日补跑论文周报 |
| 追踪其他方向 | 追踪“检索增强生成”方向的论文（须已存在对应 profile） |

补跑时脚本以 `--today` 覆盖运行日，覆盖窗口仍按滚动 7 天计算。

新增业务线时，以 `assets/profiles/customer-service.json` 为模板新建 profile，并调整关键词、arXiv 分类与相关性锚点。

## 输出约定

周报为单个本地 HTML 文件，结构固定：

| 组成部分 | 内容 |
|---|---|
| 顶部结论 | 本批论文的贯穿性判断，并说明每篇在该判断中的位置 |
| 逐篇卡片 | 英文原标题（链接至原文）、中文意译标题、相关性评分（1–5）、四段式解读 |
| 覆盖窗口 | 本期起止日期 |

四段式解读的字段与归属如下：

| 字段 | 归属 | 内容 |
|---|---|---|
| 论文要解决的问题 | 论文本身 | 通用领域面临的问题及其难点 |
| 论文方法 | 论文本身 | 解决思路与机制，以及关键结果（标注指标口径与适用范围） |
| 对业务线的价值 | 业务线 | 方法或结论迁移至业务线可解决的实际问题 |
| 论文方法的局限 | 论文本身 | 方法边界、未解决问题，以及迁移前须验证的前提 |

各角色的建议阅读重点：

| 角色 | 阅读重点 | 用途 |
|---|---|---|
| 产品 | 顶部结论与“对业务线的价值” | 判断是否立项或试点 |
| 研发 | “论文方法”与“论文方法的局限” | 评估工程前置条件与失败模式 |
| 算法 | 问题建模、评测口径与入选理由 | 对齐研究方向 |

周报仅呈现入选论文，不列出未入选论文的数量或清单，不保留空栏目。

## 目录结构

```text
paper-intelligence/
├── SKILL.md                      # 入口：职责、周期口径与执行流程
├── install.sh                    # 安装与导出脚本
├── requirements.txt              # Python 依赖
├── assets/
│   ├── profiles/
│   │   └── customer-service.json # 检索对象：客服 Agent
│   └── report-template.html      # 周报模板
├── references/
│   ├── source-rules.md           # 信源、覆盖窗口与筛选规则
│   ├── analysis-style.md         # 四段式写法、归属与数字规则
│   └── self-test.md              # 变更后的自测清单
└── scripts/
    ├── resolve_week.py           # 计算覆盖窗口
    ├── fetch_papers.py           # 抓取与去重
    ├── validate_selection.py     # 结构与归属校验
    └── render_report.py          # 渲染 HTML 周报
```

## 贡献

欢迎提交 Issue 与 Pull Request。修改脚本、模板、依赖或 profile 时，须按 [自测清单](references/self-test.md) 完成对应检查，并记录输入、命令与实际结果。贡献者名单见 [CONTRIBUTORS.md](CONTRIBUTORS.md)。

## 许可证

[MIT](LICENSE)
