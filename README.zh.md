# swarma

AI agent 与 swarm 的增长实验循环。

**[swarma.dev](https://swarma.dev)**

[English](README.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [한국어](README.ko.md) | [Deutsch](README.de.md)

---

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

你的 agent 在执行任务。swarma 让它们改为运行 A/B 测试。

定义一个假设和一个指标。swarma 负责整个循环：运行实验、评估结果、给出判定、更新策略。经过足够多的迭代后，你将获得一本经过验证的实战手册——记录的是真正有效的方法，而非你以为会有效的方法。

```
strategy.md → 执行 → 度量 → 判定 → 更新后的 strategy.md
     ↑                                              |
     └──────────────────────────────────────────────┘
```

融合了 [QMD](https://github.com/glitch-rabin/qmd) 和 [karpathy autoresearch 模式](https://github.com/karpathy/autoresearch) 的实践经验——增长团队一直在用的实验循环，现在应用于 AI agent swarm。

## 为什么做这个

每个在 Uber、Spotify、Facebook、Airbnb 的增长团队都跑同一套循环：假设、测试、度量、学习、重复。胜出的团队并不更聪明——他们只是跑了更多实验，并且真正尊重数据。经历上千个循环后沉淀下来的实战手册才是真正的资产。不是团队，不是工具，不是那些聪明的想法。是复合积累的认知。

瓶颈一直是人力带宽。即使最好的增长团队每周也只能跑 2-5 个实验。你需要人来设计测试、执行、等待结果、分析、撰写总结、更新手册。大多数团队因为时间不够而跳过一半步骤。

做了 10 年增长团队的搭建和扩张后，规律很明显：循环本身没问题。瓶颈在于你能跑多少次。AI agent 彻底消除了这个瓶颈。一个 swarm 在人类团队跑 2 个实验的时间里可以跑 50 个。但前提是有东西在真正闭合这个循环——评估结果、给出判定、演化策略。

这就是 swarma 做的事。规模化增长团队视为理所当然的实验基础设施，打包成任何 agent swarm 都能用的工具。同样的循环、同样的严谨、同样的复利效应。无限次迭代。不需要 50 人的团队。

## 快速开始

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma
pip install -e .
```

```bash
swarma init                    # 创建实例 + 初始团队
swarma cycle starter           # 运行一个循环，看看效果
swarma status                  # 费用、运行次数、实验统计
```

需要 Python 3.11+ 和一个 [OpenRouter](https://openrouter.ai/) API key。不需要 GPU，不需要 PostgreSQL，不需要 Docker。笔记本电脑或 $5 的 VPS 就能跑。

## 循环如何运作

1. agent 在每次运行前读取自己的 `strategy.md`
2. 产出输出（内容、研究、分析——取决于团队做什么）
3. 一个低成本 LLM 根据 agent 的指标对输出打分（1-10 分，强制小数）
4. 分数 + 推理过程记录到 `results.tsv`
5. 达到 `min_sample_size` 次循环后（默认 3-5 次），自动给出判定
6. `strategy.md` 根据学到的内容更新
7. 下一次循环使用演化后的策略

**评分机制**：每份输出由一个独立的 LLM 调用评估，使用路由表中最便宜的模型。评估器看到输出内容、当前策略、最近 5 次分数和指标定义。返回精确分数（7.3 而不是 7）加上推理过程和策略建议。

**判定机制**：样本量足够后，swarma 将实验平均分与基线对比。提升超过 20% = **保留**（模式验证通过，策略更新）。下降超过 20% = **丢弃**（回滚）。介于两者之间 = **不确定**（已记录，需更多数据再试）。

经过几轮实验后，你的 `strategy.md` 会变成这样：

```markdown
## Validated (Exp 5)
contrarian opening + specific numbers in first line
> 23% improvement over baseline. keep this pattern.

## Inconclusive (Exp 2)
story-led hooks vs data-led hooks -- no significant difference (avg=8.1 vs baseline=7.9)
> next: increase sample size, results may be noise
```

实战手册不断成长。团队不断变聪明。你什么都不用动。

## 团队即配置

一个团队就是一个文件夹。不需要写代码。

```
teams/my-squad/
├── team.yaml          # 目标、流程、调度、预算
├── program.md         # 团队上下文和约束条件
└── agents/
    ├── researcher.yaml
    └── writer.yaml
```

```yaml
# team.yaml
name: my-squad
goal: find what works.
flow: "researcher -> writer"
schedule: "0 8 * * 1-5"
```

```yaml
# agents/writer.yaml
id: writer
name: Writer
instructions: |
  turn research into a post. max 200 words.
  hook in the first line. practitioner voice.
metric:
  name: content_quality
  target: 8.0
experiment_config:
  min_sample_size: 5
  auto_propose: true
```

模型、工具和专家视角在 `config.yaml` 中配置。agent 继承默认值或按需覆盖。

流程 DSL 支持顺序执行（`a -> b`）、并行执行（`a -> [b, c, d]`）和混合管道。

## 10 个示例小队

即用型小队在 [`examples/`](examples/) 目录下。复制一个到你的实例中并运行：

```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/
swarma cycle hook-lab
```

| 小队 | 测试内容 |
|------|---------|
| `hook-lab` | 开头语——什么能让人停下滑动 |
| `format-wars` | 轮播图 vs 纯文字 vs 线程 vs 图片 |
| `voice-finder` | 调整语气直到互动率达峰 |
| `cta-optimizer` | 行动号召的位置和措辞 |
| `topic-radar` | 你的受众真正关心哪些话题 |
| `timing-lab` | 发布时间和频率实验 |
| `repurpose-engine` | 如何在不同平台复用高表现内容 |
| `thread-lab` | 线程结构和开头模式 |
| `newsletter-lab` | 邮件标题、发送时间、格式 |
| `defi-alpha` | 加密内容的研究深度 vs 速度 |

每个小队都包含 `program.md`，提供真实的实验模式和指标指导。

## 集成

### Hermes Agent

swarma 暴露了一个 MCP server。连接到 [Hermes](https://github.com/nousresearch/hermes-agent)，你的 agent 就获得了一个专属实验团队，在它休眠时持续学习。

```yaml
# hermes config.yaml
mcp_servers:
  swarma:
    transport: stdio
    command: swarma
    args: ["serve", "--mcp"]
```

Hermes 保持简洁——设定方向、审批计划、问"我们学到了什么？"swarma 负责脏活累活。

### Claude Code / Claude Desktop

```json
{
  "mcpServers": {
    "swarma": {
      "command": "swarma",
      "args": ["serve", "--mcp"]
    }
  }
}
```

### REST API

```bash
swarma serve --port 8282        # 30+ 个端点，OpenAPI 文档在 /docs
```

### 任意 MCP 客户端

```bash
swarma serve --mcp              # stdio
swarma serve --mcp --mcp-port 8383   # HTTP
```

**注意**：作为 MCP 子进程运行时，需要在 MCP 配置的 `env` 块中传入 `OPENROUTER_API_KEY`——实例的 `.env` 文件不会被子进程继承。

## 知识层 (QMD)

agent 通过 strategy.md 进行个体学习。要实现*跨团队*学习，添加 [QMD](https://github.com/glitch-rabin/qmd)——一个索引所有 agent 输出的搜索引擎。BM25 + 向量检索 + 重排序。不需要 GPU。

```bash
pip install qmd
qmd init
qmd serve                          # http://localhost:8181
```

```yaml
# config.yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8181/mcp
```

每个 agent 的输出会被自动索引。agent 可以搜索其他 agent 学到的东西。实验循环获得了共享记忆。

不使用 QMD 时，swarma 使用本地 SQLite（仅元数据）。使用 QMD 后，可对所有输出、策略和结果进行全语义搜索。

## swarma 不是什么

- **不是记忆系统** —— [honcho](https://github.com/plastic-labs/honcho) 做记忆。swarma 做学习循环。
- **不是自动化工具** —— n8n/make 做工作流。swarma 跑实验。
- **不是 prompt 模板库** —— [agency-agents](https://github.com/msitarzewski/agency-agents) 有 135 个模板。swarma 教它们什么真正有效。
- **不是编排框架** —— CrewAI/AutoGen 跑管道。swarma 添加了让管道持续改进的反馈循环。

## 路线图

- [ ] 专家推理视角（可组合的思维框架）
- [ ] 仪表盘 UI（实验查看器、实战手册、策略演化）
- [ ] 外部指标接入（webhook、分析回调）
- [ ] 小队市场
- [ ] `pip install swarma` 发布到 PyPI

## 贡献

swarma 还在早期。如果你对 agent 的实验循环感兴趣，欢迎提 issue 或 PR。

## 许可证

MIT
