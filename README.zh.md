# swarma

增长飞轮，自动化运行。

**[swarma.dev](https://swarma.dev)**

[English](README.md) | [中文](README.zh.md) | [日本語](README.ja.md)

---

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![PyPI](https://img.shields.io/pypi/v/swarma)

你的智能体在执行任务。swarma 让它们转而运行增长实验。

描述你想改进的目标。swarma 生成团队，注入真实的增长知识，运行实验，评估结果，发布裁决，并迭代策略。经过足够多的循环，你将获得一本经过验证的 playbook，记录真正有效的方法。

一个文件夹 = 一个团队。一个循环 = 一个实验。playbook 自动生成。

## GROWS 循环

每个循环都遵循 GROWS -- 五个步骤，没有例外：

```
  Generate       Run         Observe       Weigh        Stack
 生成假设 --> 运行实验 --> 观察信号 --> 权衡裁决 --> 累积策略
     ^                                                  |
     └──────────────────────────────────────────────────┘
```

| 步骤 | 具体操作 |
|------|---------|
| **G -- Generate（生成）** | 智能体读取其 `strategy.md`，提出假设。"反直觉的开头将在收藏指标上超过数据驱动的钩子。" |
| **R -- Run（运行）** | 智能体在假设激活的状态下执行。产出输出 -- 研究、文案、分析，取决于团队的职能。 |
| **O -- Observe（观察）** | 一个独立的 LLM 根据智能体的目标指标对输出进行评分（1-10 分，强制使用小数）。分数 + 推理过程记录到 `results.tsv`。 |
| **W -- Weigh（权衡）** | 在达到 `min_sample_size` 个循环（默认 3-5 个）后，swarma 将实验均值与基线进行比较。提升 >20% = **保留**。下降 >20% = **丢弃**。介于两者之间 = **待定**。 |
| **S -- Stack（累积）** | 经过验证的模式被写回 `strategy.md` 并推送到共享 playbook。下一个循环基于迭代后的策略生成新假设。 |

这与 Uber、Spotify 和 Airbnb 的增长团队所运行的循环完全相同。胜出的团队并非更聪明 -- 他们运行更多实验并尊重数据。swarma 消除了人力带宽瓶颈。一个集群运行 50 个实验的时间，人类团队只能运行 2 个。

## 快速开始

```bash
pip install swarma
```

或从源码安装：

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma && pip install -e .
```

```bash
swarma init                                        # 创建实例 + 初始团队
swarma cycle starter --topic "why do startups fail?"   # 运行一个循环
swarma status                                      # 查看成本、运行次数、实验状态
```

需要 Python 3.11+ 和一个 [openrouter](https://openrouter.ai/) API 密钥。无需 GPU，无需 PostgreSQL，无需 Docker。在笔记本电脑或 $5 的 VPS 上即可运行。

## 从目标生成团队

不要手动配置智能体。描述你的目标，swarma 自动构建团队。

```bash
swarma team create my-growth --from-goal "improve landing page conversion rate"
```

这会调用 LLM 来设计一个团队，包含合适的智能体、流程、模型以及第一个实验假设。生成的团队包括：

- `team.yaml` -- 目标、流程、预算
- `agents/*.yaml` -- 各智能体的独立配置和具体指令
- `program.md` -- 实验模式和约束条件
- 一个可以直接运行的首个实验

添加业务上下文以获得更好的结果：

```bash
swarma team create growth-lab \
  --from-goal "optimize our signup funnel" \
  --context "B2B SaaS, 500 free users, 2% conversion to paid" \
  --budget 50
```

## 循环的详细工作方式

GROWS 循环的实际运作：

1. 智能体在每次运行前读取其 `strategy.md`
2. 产出输出（研究、文案、分析 -- 取决于团队的职能）
3. 一个低成本 LLM 根据智能体的指标对输出进行评分（1-10 分，强制使用小数）
4. 分数 + 推理过程记录到 `results.tsv`
5. 在达到 `min_sample_size` 个循环（默认 3-5 个）后，自动发布裁决
6. `strategy.md` 根据学到的内容进行更新
7. 下一个循环使用迭代后的策略

**评分机制**：每个输出由一个独立的 LLM 调用进行评估，使用路由表中最便宜的模型。评估者看到输出内容、当前策略、最近 5 次评分以及指标定义。返回精确分数（7.3，不是 7）加上推理过程和策略建议。

**裁决机制**：在收集到足够样本后，swarma 将实验均值与基线进行比较。提升 >20% = **保留**（模式验证通过，策略已更新）。下降 >20% = **丢弃**（已回滚）。介于两者之间 = **待定**（已记录，需要更多数据后重试）。

经过几轮实验后，你的 `strategy.md` 从种子知识演变为经过验证的模式：

```markdown
## Validated (Exp 5)
反直觉的开头 + 首行使用具体数字
> 比基线提升 23%。保留此模式。

## Inconclusive (Exp 2)
故事驱动的钩子 vs 数据驱动的钩子 -- 无显著差异 (avg=8.1 vs baseline=7.9)
> 下一步：增加样本量，结果可能是噪声
```

## 接入真实指标

LLM 自我评估是初始代理指标。在生产环境中，应接入真实世界信号：

```bash
# 记录单个指标
swarma metric log hook-lab copywriter 4.2 --metric ctr_pct

# 关联到特定实验
swarma metric log hook-lab copywriter 127 --metric impressions --exp 3

# 从 CSV 批量导入
swarma metric import hook-lab metrics.csv

# 查看已记录的指标
swarma metric show hook-lab
```

CSV 格式：`agent,value,metric_name,note`

指标自动关联到智能体的当前活跃实验。当外部指标和 LLM 评分同时可用时，实验循环会同时使用两者。

## 预置策略

智能体不是从零开始。每个小队都包含一个 `strategy.md`，预置了真实的增长知识 -- 经过验证的模式、反面模式以及待测试的假设。GROWS 循环会随时间不断优化这些内容。

来自 hook-lab 策略的示例：

```markdown
### Validated Patterns

**具体性胜出**
- 包含具体数字的钩子在收藏指标上比模糊声明高出 2-3 倍
- "47% 的初创公司" > "大多数初创公司"

**损失框架 > 收益框架**
- "你每月损失 $X" 在点击率上优于 "你每月可以节省 $X"
- 例外：面向有抱负的受众时，收益框架效果更好

### Patterns to Test
- [ ] 第一人称自白 vs 第三人称案例研究
- [ ] 时间锚定（"在 2024 年..."）vs 永恒型钩子
```

## 团队即配置

一个团队就是一个文件夹。无需代码。

```
teams/my-squad/
├── team.yaml          # 目标、流程、调度、预算
├── program.md         # 团队上下文和约束条件
└── agents/
    ├── researcher.yaml
    ├── writer.yaml
    └── strategy.md    # 预置增长知识
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

模型、工具和专家视角在 `config.yaml` 中配置。智能体继承默认值或按智能体级别覆盖。

流程 DSL 支持顺序执行 (`a -> b`)、并行执行 (`a -> [b, c, d]`) 和混合管道。

## 18 个小队模板

在 [`examples/`](examples/) 中提供开箱即用的小队，每个都包含预置策略：

```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/
swarma cycle hook-lab
```

**核心增长小队：**

| 小队 | AARRR 阶段 | 测试内容 | 智能体数 |
|------|-----------|---------|---------|
| `hook-lab` | 获客 | 开头文案 -- 什么能让用户停下滑动 | 3 |
| `landing-lab` | 获客 | 落地页文案和结构 | 3 |
| `seo-engine` | 获客 | 搜索可见性和内容排名 | 3 |
| `cold-outbound` | 获客 | 外发消息和序列 | 3 |
| `channel-mix` | 获客 | 多平台内容策略 | 3 |
| `activation-flow` | 激活 | 注册到价值的引导流程 | 3 |
| `pricing-lab` | 收入 | 定价展示和套餐设计 | 3 |
| `retention-squad` | 留存 | 流失信号和召回模式 | 3 |
| `referral-engine` | 推荐 | 病毒循环和邀请机制 | 3 |
| `competitive-intel` | -- | 市场监控和定位 | 3 |

**2026 增长运营小队：**

| 小队 | 测试内容 | 智能体数 |
|------|---------|---------|
| `faceless-factory` | 自动化短视频生产管线 | 3 |
| `ad-creative-lab` | 规模化效果素材测试 | 3 |
| `ugc-factory` | 用户生成内容模拟 | 3 |
| `programmatic-seo` | 规模化自动 SEO 内容 | 3 |
| `newsletter-engine` | 邮件通讯增长 + 留存 | 3 |
| `acquisition-squad` | 付费 + 自然获客循环 | 3 |
| `community-engine` | 社区驱动增长自动化 | 3 |
| `agentic-storefront` | AI 驱动的电商优化 | 3 |

每个小队都包含一个 `program.md`（实验模式）和一个 `strategy.md`（真实增长知识作为起始基线）。

## QMD 知识层

智能体通过 strategy.md 单独学习。这是单团队学习。要实现*跨团队*学习，需要接入 [QMD](https://github.com/tobi/qmd) -- 一个索引所有智能体输出的知识引擎。BM25 + 向量检索 + 重排序。无需 GPU。

```bash
npm install -g @tobilu/qmd
qmd init
qmd serve                          # http://localhost:8181
```

```yaml
# config.yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8181/mcp
```

每个智能体的输出都会自动被索引。智能体可以搜索其他智能体学到的内容。GROWS 循环获得了共享记忆。

当一个实验获得 **保留** 裁决时，经过验证的模式会被保存到跨团队的 `playbook` 集合中。每个智能体都能看到来自所有其他团队的已验证模式。反面模式（被丢弃的实验）也会被追踪，这样团队可以避免重复已经失败的尝试。

```bash
# 跨所有已验证模式的语义搜索
curl localhost:8282/playbook/search?q=hook+specificity
```

这就是复利机制。团队 A 发现损失框架优于收益框架。团队 B（运行着完全不同的实验）在其上下文窗口中看到该模式并将其纳入。知识只进不退，持续积累。

## Hermes 集成

swarma 的设计初衷是与 [Hermes](https://github.com/nousresearch/hermes-agent) 作为运营层协同工作。Hermes 保持简洁 -- 设定方向，审批计划，追问"我们学到了什么？"swarma 在底层执行繁重的工作。

swarma 暴露一个包含 22 个工具的 MCP 服务器。连接后，你的 Hermes 智能体就拥有了一个完整的增长团队，在它休眠时持续运行实验。

```yaml
# hermes config.yaml
mcp_servers:
  swarma:
    transport: stdio
    command: swarma
    args: ["serve", "--mcp"]
```

运营模式：Hermes 定义目标和约束条件。swarma 生成团队，运行 GROWS 循环，呈现裁决结果。Hermes 阅读 playbook 并决定下一步行动。运营者永远不直接接触实验基础设施。

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
swarma serve --port 8282        # 30+ 个端点，OpenAPI 文档位于 /docs
```

### 任意 MCP 客户端

```bash
swarma serve --mcp                     # stdio
swarma serve --mcp --mcp-port 8383     # HTTP
```

**注意**：作为 MCP 子进程运行时，需要在 MCP 配置的 `env` 块中传递 `OPENROUTER_API_KEY` -- 实例的 `.env` 文件不会被子进程继承。

## swarma 不是什么

- **不是记忆系统** -- [honcho](https://github.com/plastic-labs/honcho) 负责记忆。swarma 负责学习循环。
- **不是自动化工具** -- n8n/make 负责工作流。swarma 负责运行实验。
- **不是提示词库** -- [agency-agents](https://github.com/msitarzewski/agency-agents) 有 135 个模板。swarma 通过反馈循环教会它们什么有效。
- **不是编排框架** -- crewai/autogen 负责运行管道。swarma 添加的 GROWS 循环让管道持续改进。

区别在于：提示词模板告诉智能体做一次什么。swarma 教会它什么长期有效。模板是起点。playbook 是输出。

## 站在巨人的肩膀上

swarma 的诞生源于三个人的三个理念：

- **[autoresearch](https://github.com/karpathy/autoresearch)**，Andrej Karpathy 所创 -- 自动化研究循环的模式，智能体在其中反复优化方法。swarma 将这一理念应用于增长实验而非研究论文。
- **[QMD](https://github.com/tobi/qmd)**，Tobi Lutke ([@tobi](https://x.com/tobi)) 所创 -- 智能体之间的共享知识。其洞察在于：处理不同问题的智能体应该能够相互学习。swarma 的跨团队 playbook 层正是建立在这一理念之上。
- **[Hermes](https://github.com/nousresearch/hermes-agent)**，NousResearch ([@NousResearch](https://x.com/NousResearch)) 所创 -- 运营层。其理念是一个智能体应该能够通过工具使用来指挥专家智能体团队。swarma 的设计定位就是 Hermes 所运营的基础设施。

## 路线图

**已完成：**

- [x] GROWS 实验循环（生成 -> 运行 -> 观察 -> 权衡 -> 累积）
- [x] 专家推理视角（34 个可组合的思维框架）
- [x] 仪表盘 UI（实验查看器、playbook、策略演进）
- [x] 团队生成器 (`swarma team create --from-goal`)
- [x] 外部指标接入 (`swarma metric log/import/show`)
- [x] 预置策略文件，包含真实增长知识
- [x] `pip install swarma` 已发布至 PyPI (v0.2.0)
- [x] QMD 跨团队连接（裁决 -> playbook -> 共享知识）
- [x] 18 个小队模板，覆盖完整 AARRR 漏斗 + 2026 增长运营
- [x] 反面模式追踪（丢弃裁决保存至 playbook）
- [x] `/playbook/search` 通过 QMD 实现跨团队语义搜索
- [x] MCP 服务器（22 个工具），支持 Hermes / Claude Code / 任意客户端
- [x] `--topic` 标志，支持临时循环

**下一步：**

- [ ] Webhook 指标接入（实时分析回调）
- [ ] Hermes 技能中心 + OpenClaw 市场发布
- [ ] 小队市场（分享和发现已验证的团队 + playbook）
- [ ] HuggingFace 数据集作为小队知识种子
- [ ] 观察模式实验（真实世界信号优先，LLM 评估辅助）

## 贡献

swarma 仍处于早期阶段。如果你对智能体实验循环感兴趣，欢迎提交 issue 或 PR。

## 许可证

MIT
