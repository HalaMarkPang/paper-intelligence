# Paper Intelligence · 论文周报 Skill

按指定业务方向，抓取 arXiv 与 HuggingFace 在指定周期内的相关论文，逐篇产出四段式解读（论文要解决的问题、论文方法、对业务线的价值、论文局限），渲染为 HTML 周报。默认追踪方向为**客服 Agent**。

面向：**产品 / 研发 / 算法**——产品看迁移价值与决策线索，研发看可落地的方法边界，算法看问题建模与评测口径。

**维护者**：[HalaMarkPang](https://github.com/HalaMarkPang)（群）  
**License**：MIT

## 快速开始

前提：Python 3.9+，以及 Claude Code / Cursor / Codex 等可加载 Agent Skill 的客户端。本机需能访问 HuggingFace Daily Papers 与 arXiv。

```bash
git clone https://github.com/HalaMarkPang/paper-intelligence.git
cd paper-intelligence
bash install.sh
```

安装会校验 Python、安装 `jinja2`，并导出到 `~/.agent-skills/paper-intelligence`；若本机有 Claude Code，会额外软链到 `~/.claude/skills/paper-intelligence`。

在会话中用自然语言触发即可，例如：

- 「跑一下论文周报」「本周论文」
- 「论文周报跑一下 8 月第二周的」
- 「追踪一下 XX 方向的论文」（需先有对应 profile）

验证环境：

```bash
python3 scripts/resolve_week.py
```

正常会输出形如 `{"period_start": "...", "period_end": "...", ...}`。

## 产出物

一份本地 HTML 周报：

- **顶部结论**：本批论文的贯穿性判断，及每篇在逻辑链上的位置
- **逐篇卡片**：英文标题（可点进原文）、中文意译、相关性评分（1–5）、四段式解读
- **覆盖窗口**：上周三 00:00:00 至本周二 23:59:59（建议周三跑，正好盖满一整周）
- **入选上限**：默认 10 篇，相关性优先，不足不强凑

归属规则：论文问题 / 方法 / 局限只写论文本身；业务线名称只允许出现在「对业务线的价值」一段。

## 给谁用、怎么用

| 角色 | 怎么用这份周报 |
|------|----------------|
| 产品 | 看 `inspiration` 与顶部 digest，判断哪些方法值得立项或试点 |
| 研发 | 看方法与局限段，评估工程前置条件与失败模式 |
| 算法 | 看问题建模、评测口径与 `relevance_reason`，对齐研究方向 |

换业务线：复制 `assets/profiles/customer-service.json` 改关键词与锚点即可，脚本与编排层不用动。详细流程见 [`SKILL.md`](SKILL.md)。

## 限制

1. **人工触发**，不支持无人值守定时（分析由 Agent 在会话中完成，禁止调外部 LLM API）。
2. **周期固定为周口径**（上周三至本周二），不是滚动 7 天。
3. HuggingFace Daily Papers 是主力源；arXiv RSS 多为近一两天补强，补历史周时可能为 0，属正常。
4. 产出是本地 HTML，不自动发到文档或群里。

## 依赖

见 [`requirements.txt`](requirements.txt)。必备仅 `jinja2`；`certifi` 可选（HTTPS 证书）。其余脚本用 Python 标准库。

## 仓库说明

本仓库为独立公开版，与其他内部 skills 仓各自演进，不保证双向同步。
