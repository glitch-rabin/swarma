# swarma

[English](README.md) | **中文** | [日本語](README_JA.md)

自主学习的智能体团队。

---

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

swarma 是一个构建自主智能体团队的框架，团队通过实验不断优化自身策略。每个智能体拥有一个指标、一份可编辑的策略文件，以及一个基于实测结果持续迭代的学习循环。

这是 [Karpathy autoresearch 模式](https://github.com/karpathy/autoresearch) 在智能体团队中的应用 -- 不同之处在于，这些智能体优化的是真实工作流，而不是训练过程。

## 工作原理

```
strategy.md → 执行 → 度量 → 裁决 → 更新后的 strategy.md
     ↑                                              |
     └──────────────────────────────────────────────┘
```

1. 每个智能体在运行前读取自己的 `strategy.md`
2. 产出内容（文案、研究、分析 -- 取决于团队职能）
3. 根据目标指标评估产出质量
4. 将评分记录到 `results.tsv`
5. 样本量足够后，发出裁决：**保留 (keep)**、**丢弃 (discard)** 或 **不确定 (inconclusive)**
6. 将学到的经验写入 `strategy.md`
7. 下一轮循环使用进化后的策略

## 快速开始

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma
pip install -e .
```

```bash
# 初始化实例，包含一个入门团队
swarma init

# 添加 API 密钥
echo "OPENROUTER_API_KEY=sk-or-..." > ~/.swarma/instances/default/.env

# 运行一轮循环
swarma run --once

# 或持续运行，开启定时调度 + API 服务
swarma run --port 8000
```

## 环境要求

- Python 3.11+
- 一个 [OpenRouter](https://openrouter.ai/) API 密钥
- 就这些。不需要 GPU，不需要 PostgreSQL，不需要 Docker。

SQLite 管理状态，Markdown 文件存储知识。笔记本电脑或 $5/月的 VPS 即可运行。

## 团队即配置

团队就是一个包含 YAML 配置的文件夹，不需要写代码。

```
teams/content-ops/
├── team.yaml              # 目标、流程、调度、预算
├── program.md             # 团队背景与约束
└── agents/
    ├── researcher.yaml    # 模型、指标、指令
    └── writer.yaml
```

**team.yaml**
```yaml
name: Content Operations
goal: produce practitioner-grade content worth saving.
flow: "researcher -> writer"
schedule: "0 7 * * *"     # 每天早上 7 点
budget_monthly: 50.0
```

**智能体配置**
```yaml
id: writer
name: Content Writer
model:
  model_id: qwen/qwen3.5-plus-02-15
  max_tokens: 1500
  temperature: 0.7
instructions: |
  turn research into a linkedin post. max 200 words.
  hook in the first line. practitioner voice. no emojis.
metric:
  name: content_quality
  target: 8.0
experiment_config:
  min_sample_size: 3
  auto_propose: true
```

## 示例团队

14 个开箱即用的团队配置在 [`examples/`](examples/)，按职能分类：

| 分类 | 团队 | 流程 | 功能 |
|------|------|------|------|
| **内容与增长** | `content-ops` | researcher -> writer | 研究 + LinkedIn 帖子 |
| | `social-growth` | researcher -> growth-lead -> [linkedin, twitter, newsletter] | 多平台内容分发 |
| | `seo-lab` | keyword-researcher -> content-writer -> seo-auditor | SEO 内容实验 |
| | `thought-leadership` | research-analyst -> essay-writer -> editor | 深度权威内容 |
| **研究与情报** | `market-intel` | scanner -> analyst -> briefer | 竞争情报 |
| | `trend-scout` | monitor -> analyst -> reporter | 新兴趋势检测 |
| | `crypto-research` | data-collector -> analyst -> strategist | DeFi 市场分析 |
| **转化** | `email-ops` | researcher -> copywriter -> subject-line-tester | 邮件营销优化 |
| | `landing-copy` | researcher -> copywriter -> critic | 落地页文案 A/B 测试 |
| **运营** | `quality-lab` | auditor | 跨团队质量评估 |
| | `model-lab` | prompt-engineer -> evaluator | 模型对比基准测试 |
| | `cost-optimizer` | tester -> analyst | 在质量达标前提下最小化成本 |
| **专项** | `dev-rel` | docs-researcher -> tutorial-writer -> code-reviewer | 开发者教程 |
| | `product-growth` | analyst -> hypothesis-generator -> experiment-designer | 增长实验设计 |

每个团队是一个文件夹，复制到你的实例中即可使用和定制。`swarma init --template content-ops` 可从任意示例初始化。

## 实验循环

每个定义了 `metric` 的智能体都会自动获得学习循环：

```
teams/content-ops/results/writer/
├── strategy.md              # 可编辑，随时间进化
├── results.tsv              # 只追加的评分日志
└── experiments/
    └── exp-001.md           # 详细实验记录
```

**strategy.md** 在每次实验后更新：
```markdown
# 当前策略

尚未设定策略。等待首次实验。

## 不确定 (实验 2)
尝试：在每篇帖子中添加具体的下一步行动 -- 无显著变化 (均值=7.9 vs 基线=7.8)
> 下一步：对比行业基准以获取更多上下文

## 已验证 (实验 5)
反直觉开头 + 首行使用具体数字
> 比基线提升 23%。保留该模式。
```

策略手册持续增长，团队越来越聪明，你无需干预。

## 度量

默认情况下，智能体使用低成本 LLM 调用进行自我评估。这足以用于原型验证和启动循环。

生产环境中，接入真实信号：

```yaml
# 智能体配置 -- 外部指标回调
metric:
  name: linkedin_saves
  target: 50
  source: webhook    # 接受 POST 请求 {output_id, score}
```

```bash
# 将真实分析数据推送回循环
curl -X POST http://localhost:8282/metrics \
  -d '{"agent": "writer", "output_id": "cycle-001", "score": 47}'
```

自我评估让你快速迭代，外部信号让你优化真正重要的指标。

## 流程 DSL

定义智能体管线：

```yaml
# 顺序执行
flow: "researcher -> writer"

# 并行执行
flow: "researcher -> [linkedin-writer, twitter-writer, visual-designer]"

# 混合模式
flow: "[research-analyst, intelligence-agent] -> growth-lead -> [linkedin-writer, twitter-writer] -> analytics"
```

并行步骤通过 `asyncio.gather()` 执行。第 N 步的输出作为第 N+1 步的上下文。

## 多模型路由

swarma 通过 [OpenRouter](https://openrouter.ai/) 将任务路由到最合适的模型。300+ 模型可选，按 token 计费。

```yaml
# config.yaml 中的默认路由表（可按智能体覆盖）
models:
  routing:
    cheap: mistralai/mistral-nemo
    writing: qwen/qwen3.5-plus-02-15
    research: perplexity/sonar-pro
    reasoning: deepseek/deepseek-r1
    planning: anthropic/claude-sonnet-4-6
```

每个智能体可在其配置中覆盖模型。成本按智能体、团队、天维度追踪。

## 共享知识 + QMD

所有团队共享知识库。智能体将产出写成带 YAML frontmatter 的 Markdown 文件，并建立索引以供搜索。

默认使用 SQLite 元数据查询 -- 开箱即用，零配置。生产环境中，连接 [QMD](https://github.com/tobi/qmd)（Tobi Lutke 开发）以解锁完整语义搜索：

```yaml
# config.yaml
knowledge:
  qmd_endpoint: http://localhost:8181    # BM25 + 向量 + 重排序
  collections: [research, content, experiments, briefs]
```

连接 QMD 后，智能体获得：
- **BM25 + 向量 + 重排序** 搜索所有团队的所有产出
- **按集合限定搜索**（例如仅搜索 `research` 产出）
- **跨团队知识传递** -- 团队 A 的研究成果自动为团队 B 的决策提供信息

知识在整个实例中持续积累。不连接 QMD 也能正常工作 -- 只是使用更简单的元数据匹配。

## 运行时适配器

智能体不一定是 LLM 调用。swarma 支持四种运行时：

| 运行时 | 用途 | 配置 |
|---------|------|------|
| `llm`（默认） | 通过 OpenRouter 直接调用 LLM | 智能体 YAML 中的模型配置 |
| `hermes` | [Hermes Agent](https://github.com/nousresearch/hermes-agent)，具备完整工具访问能力 | endpoint + api_key |
| `http` | 任何接受 JSON 的 HTTP 端点 | endpoint + headers |
| `process` | 本地 CLI 命令，stdin/stdout JSON | command + timeout |

## 集成方式

swarma 通过两个方向连接你的技术栈：智能体通过运行时适配器**向外调用**，外部系统通过 MCP 或 REST **向内接入**。

**Hermes Agent** -- 最深度的集成。Hermes 智能体获得完整工具访问，swarma 负责编排和学习。也可以反过来：将 Hermes 连接到 swarma 的 MCP 服务器，从 Telegram/Discord 触发循环。

**Claude Code / Claude Desktop** -- 将 swarma 添加为 MCP 服务器。Claude 获得运行循环、查看实验、阅读策略手册、审批计划的工具。

```json
{
  "mcpServers": {
    "swarma": {
      "command": "swarma",
      "args": ["serve", "--mcp", "--instance", "my-swarm"]
    }
  }
}
```

**任何 MCP 客户端** -- stdio 或 HTTP 传输：

```bash
swarma serve --mcp                          # stdio
swarma serve --mcp --mcp-port 8383          # HTTP
```

**REST API** -- 通过 HTTP 完全控制。OpenAPI 文档位于 `/docs`。

```bash
swarma serve --port 8282
```

## 架构

```
swarma/
├── core/           # 智能体、循环运行器、实验循环、状态、配置、知识
├── flow/           # DSL 解析器 + 异步执行器
├── adapters/       # llm、hermes、http、process 运行时
├── tools/          # 3 层注册表（实例 > 团队 > 智能体）
├── experts/        # 推理框架目录 + 组合器
├── server/         # FastAPI REST + MCP 协议服务器
└── cli/            # init、run、serve、status、team、tool 命令
```

**状态**: SQLite (outputs, experiments, cost_log, agent_runs, pending_plans, artifact_log, task_queue)

**知识**: 磁盘上的 Markdown 文件，在 SQLite 中建立索引，可选通过 QMD 搜索

**调度**: APScheduler 支持 cron 定时团队循环 + 事件驱动的心跳队列

## 设计决策

**自我评估作为默认方式。** 智能体使用低成本模型评估自己的产出。这不完美 -- 但它让循环零配置即可运行。生产环境应接入外部信号（分析数据、人工评分、API 指标）。循环机制相同，只是信号来源不同。

**Markdown 文件存储。** 策略文件、知识产出、实验日志 -- 全部可读、可编辑、可 diff、对 Git 友好。没有私有格式，没有数据库锁定。`cat strategy.md` 就能看到智能体知道的一切。

**OpenRouter 而非直连供应商 API。** 一个 API 密钥，300+ 模型，按 token 计费。在 YAML 中改一个字符串即可切换模型。无需修改 SDK，无需轮换凭证。

**YAML 团队，不用写代码。** 定义团队不应该需要 Python。非程序员借助 LLM 辅助就能创建、修改和理解团队配置。框架负责连接。

**预算跟踪，暂不强制。** 成本按智能体、团队、天维度追踪。team config 中的 `budget_monthly` 目前仅供参考 -- 不会硬性停止循环。强制执行已在计划中但尚未发布。使用 `swarma status` 查看开支。

**尚无上下文窗口管理。** 策略文件、知识检索和专家视角在 prompt 中竞争 token。目前请保持策略文件简短、知识查询精准。分层上下文加载 (L0/L1/L2) 在路线图中。

## swarma 不是什么

- **不是聊天机器人框架** -- 智能体按调度自主运行，不是响应用户消息
- **不是记忆引擎** -- [Honcho](https://github.com/plastic-labs/honcho) 做记忆。swarma 做编排 + 学习。
- **不是 Prompt 库** -- [agency-agents](https://github.com/msitarzewski/agency-agents) 有 135 个智能体模板。swarma 运行它们并教会它们什么有效。
- **不是仿真引擎** -- [MiroFish](https://github.com/666ghj/MiroFish) 做群体仿真。swarma 优化真实工作流。

## 路线图

- [x] 团队模板（14 个示例：内容、研究、转化、运营、专项）
- [ ] 仪表盘 UI（实验查看器、策略手册、智能体详情）
- [ ] 外部指标接入（webhooks、分析回调）
- [ ] Hermes Agent 集成包
- [ ] 分层上下文加载（L0/L1/L2，灵感来自 [OpenViking](https://github.com/volcengine/OpenViking)）
- [ ] PyPI 发布 `pip install swarma`

## 贡献

swarma 处于早期阶段。如果你对智能体学习循环、增长实验框架或多模型编排感兴趣，欢迎提交 Issue 或 PR。

## 许可证

MIT
