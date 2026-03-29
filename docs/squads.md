# Pre-built Squad Templates

swarma ships with 18 squad templates covering the full AARRR funnel. Each squad is a complete team: agents, flow, program, strategy seeds, and experiment patterns. Copy one into your instance, customize, and run.

## Using a Template

### Copy into your instance

```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/hook-lab
```

Or use the template system:

```bash
swarma team templates              # list available templates
swarma team create my-hooks --template hook-lab
```

### Verify it loaded

```bash
swarma team show hook-lab
```

### Run it

```bash
swarma cycle hook-lab --topic "why developers hate meetings"
```

## Squad Directory

### Acquisition

| Squad | Goal | Agents | Flow |
|-------|------|--------|------|
| [hook-lab](#hook-lab) | Find message angles that stop the scroll | researcher, copywriter, judge | researcher -> copywriter -> judge |
| [landing-lab](#landing-lab) | Find page structure that converts visitors to users | researcher, copywriter, critic | researcher -> copywriter -> critic |
| [seo-engine](#seo-engine) | Produce content that ranks | keyword-researcher, content-writer, seo-auditor | keyword-researcher -> content-writer -> seo-auditor |
| [cold-outbound](#cold-outbound) | Find outbound messages that get replies | researcher, copywriter, personalization-engine | researcher -> copywriter -> personalization-engine |
| [acquisition-squad](#acquisition-squad) | Build AI-powered outbound acquisition pipelines | researcher, sequencer, optimizer | researcher -> sequencer -> optimizer |
| [ad-creative-lab](#ad-creative-lab) | Generate and test ad creatives at scale | creative-strategist, copywriter, analyst | creative-strategist -> copywriter -> analyst |
| [programmatic-seo](#programmatic-seo) | Generate data-backed pages for long-tail queries | keyword-researcher, template-builder, quality-checker | keyword-researcher -> template-builder -> quality-checker |

### Activation

| Squad | Goal | Agents | Flow |
|-------|------|--------|------|
| [activation-flow](#activation-flow) | Get new users to the aha moment faster | researcher, sequence-designer, evaluator | researcher -> sequence-designer -> evaluator |

### Revenue

| Squad | Goal | Agents | Flow |
|-------|------|--------|------|
| [pricing-lab](#pricing-lab) | Find price point and packaging that maximizes revenue per visitor | researcher, analyst, page-writer | researcher -> analyst -> page-writer |
| [agentic-storefront](#agentic-storefront) | Optimize e-commerce for AI agent discovery and conversion | merchandiser, copywriter, analyst | merchandiser -> copywriter -> analyst |

### Retention

| Squad | Goal | Agents | Flow |
|-------|------|--------|------|
| [retention-squad](#retention-squad) | Keep users before trying to get new ones | signal-monitor, analyst, outreach-writer | signal-monitor -> analyst -> outreach-writer |

### Referral

| Squad | Goal | Agents | Flow |
|-------|------|--------|------|
| [referral-engine](#referral-engine) | Turn users into recruiters | analyst, loop-designer, outreach-writer | analyst -> loop-designer -> outreach-writer |

### Content and Distribution

| Squad | Goal | Agents | Flow |
|-------|------|--------|------|
| [channel-mix](#channel-mix) | Find which channels amplify which messages | strategist, linkedin-writer, twitter-writer, email-writer | strategist -> [linkedin-writer, twitter-writer, email-writer] |
| [newsletter-engine](#newsletter-engine) | Build and monetize a newsletter | curator, writer, growth-hacker | curator -> writer -> growth-hacker |
| [faceless-factory](#faceless-factory) | Produce high-retention faceless short-form videos | script-writer, thumbnail-designer, analytics | script-writer -> thumbnail-designer -> analytics |
| [ugc-factory](#ugc-factory) | Produce AI-generated UGC-style ad content | script-writer, reviewer, performance-tracker | script-writer -> reviewer -> performance-tracker |

### Intelligence

| Squad | Goal | Agents | Flow |
|-------|------|--------|------|
| [competitive-intel](#competitive-intel) | Know what competitors ship before their customers do | scanner, analyst, briefer | scanner -> analyst -> briefer |
| [community-engine](#community-engine) | Build engaged communities with DAU/MAU >20% | engagement-manager, content-curator, analyst | engagement-manager -> content-curator -> analyst |

---

## Squad Details

### hook-lab

**Goal**: Find the message angles that make people stop scrolling.

**Flow**: `researcher -> copywriter -> judge`

**Schedule**: Weekdays 8am | **Budget**: $30/mo

**What it does**: The researcher finds a specific topic with proof points and an emotional lever. The copywriter produces 3 hook variations (data-led, story-led, contrarian-led). The judge scores each on pattern interrupt, specificity, curiosity gap, credibility, and save-worthiness.

**Experiment patterns**: Loss vs gain framing, specific numbers vs vague claims, story lead vs data lead, contrarian vs consensus, question vs statement hooks, personal vs universal framing.

**Metrics**: hook_score (self-eval), production: save_rate, dwell_time, CTR.

---

### landing-lab

**Goal**: Find the page structure that converts visitors into users.

**Flow**: `researcher -> copywriter -> critic`

**Schedule**: Mon/Wed 10am | **Budget**: $25/mo

**What it does**: Tests landing page elements systematically. The researcher identifies conversion bottlenecks, the copywriter generates page variations, the critic evaluates against conversion principles.

**Experiment patterns**: Headline angle testing, CTA placement, social proof formats, pricing display, above-the-fold structure.

---

### seo-engine

**Goal**: Produce content that ranks, not content that exists.

**Flow**: `keyword-researcher -> content-writer -> seo-auditor`

**Schedule**: Mon/Wed/Fri 6am | **Budget**: $35/mo

**What it does**: The keyword researcher finds opportunities (volume + intent + competition gap). The content writer produces SEO-optimized content. The auditor checks technical SEO factors and content quality signals.

**Experiment patterns**: Content depth vs breadth, long-tail vs head term targeting, structure formats, internal linking strategies.

---

### cold-outbound

**Goal**: Find the outbound message that gets a reply, not a block.

**Flow**: `researcher -> copywriter -> personalization-engine`

**Schedule**: Weekdays 7am | **Budget**: $25/mo

**What it does**: The researcher identifies target segments and pain points. The copywriter generates message variations. The personalization engine adapts messages to specific recipients.

**Experiment patterns**: Pain vs opportunity framing, message length (2 vs 5 sentences), personalization depth, CTA type (soft vs hard ask), followup cadence.

**Metrics**: reply_likelihood (self-eval), production: reply_rate, positive_reply_rate, meeting_booked_rate.

---

### acquisition-squad

**Goal**: Build and optimize AI-powered outbound acquisition pipelines with multi-channel sequencing.

**Flow**: `researcher -> sequencer -> optimizer`

**Schedule**: Weekdays 8am | **Budget**: $25/mo

**What it does**: Full-funnel outbound acquisition. The researcher identifies targets and channels. The sequencer builds multi-touch sequences. The optimizer tests and refines based on conversion data.

---

### ad-creative-lab

**Goal**: Generate and test ad creatives at 10-100x human volume.

**Flow**: `creative-strategist -> copywriter -> analyst`

**Schedule**: Weekdays 9am | **Budget**: $30/mo

**What it does**: Systematic ad creative testing. The strategist identifies angles and formats. The copywriter produces variant batches. The analyst scores against CTR, ROAS, and fatigue patterns.

**Experiment patterns**: Hook format A/B, visual style testing, copy length, CTA variations, audience segment targeting.

---

### programmatic-seo

**Goal**: Generate thousands of data-backed pages targeting long-tail queries with quality gates.

**Flow**: `keyword-researcher -> template-builder -> quality-checker`

**Schedule**: Mon/Thu 6am | **Budget**: $20/mo

**What it does**: The keyword researcher finds long-tail clusters. The template builder generates page templates with real data. The quality checker prevents thin content penalties.

**Experiment patterns**: Template structure, data density, internal linking, schema markup, content uniqueness scoring.

---

### activation-flow

**Goal**: Get new users to the aha moment faster. Every extra step is a drop-off.

**Flow**: `researcher -> sequence-designer -> evaluator`

**Schedule**: Mon/Thu 10am | **Budget**: $20/mo

**What it does**: Experiments on onboarding flows. The researcher identifies where users drop off. The sequence designer proposes flow modifications. The evaluator scores against time-to-value and completion rate.

**Experiment patterns**: Step reduction, empty state messaging, progress indicators, value preview timing.

---

### pricing-lab

**Goal**: Find the price point and packaging that maximizes revenue per visitor.

**Flow**: `researcher -> analyst -> page-writer`

**Schedule**: Tue/Fri 10am | **Budget**: $20/mo

**What it does**: The researcher gathers pricing intelligence (competitor benchmarks, willingness-to-pay signals). The analyst models packaging options. The page writer generates pricing page variations.

**Experiment patterns**: Anchor pricing, plan count, feature packaging, trial vs freemium, annual vs monthly display.

---

### agentic-storefront

**Goal**: Optimize e-commerce for AI agent discovery and conversion.

**Flow**: `merchandiser -> copywriter -> analyst`

**Schedule**: Mon/Wed/Fri 8am | **Budget**: $20/mo

**What it does**: Built for the Shopify UCP / AI agent commerce wave. The merchandiser optimizes product data for machine readability. The copywriter generates AI-optimized descriptions. The analyst tracks AI-attributed conversion.

**Experiment patterns**: Structured vs narrative descriptions, pricing display in structured data, category targeting, review signal impact, UCP manifest optimization.

**Metrics**: ai_attributed_conversion_rate, ai_agent_recommendation_frequency, revenue by AI platform (ChatGPT, Copilot, Gemini).

---

### retention-squad

**Goal**: Keep users before trying to get new ones. Fix the bucket before pouring more water.

**Flow**: `signal-monitor -> analyst -> outreach-writer`

**Schedule**: Weekdays 9am | **Budget**: $25/mo

**What it does**: The signal monitor identifies churn risk patterns. The analyst prioritizes interventions. The outreach writer generates win-back and engagement messages.

**Experiment patterns**: Churn signal timing, re-engagement message angle, incentive depth, channel selection.

---

### referral-engine

**Goal**: Turn users into recruiters. The best acquisition channel is the product itself.

**Flow**: `analyst -> loop-designer -> outreach-writer`

**Schedule**: Tue/Thu 11am | **Budget**: $20/mo

**What it does**: The analyst identifies referral opportunities and incentive structures. The loop designer creates viral mechanics. The outreach writer generates referral prompts and invite messaging.

**Experiment patterns**: Incentive type (two-sided vs one-sided), timing of referral ask, invite message personalization, viral loop mechanics.

---

### channel-mix

**Goal**: Find which channels amplify which messages. Same content everywhere is lazy.

**Flow**: `strategist -> [linkedin-writer, twitter-writer, email-writer]`

**Schedule**: Weekdays 9am | **Budget**: $40/mo

**What it does**: The strategist picks an angle. Then three writers adapt it for different platforms simultaneously (parallel execution). The experiment loop compares performance across channels.

Note the parallel flow: `strategist -> [linkedin-writer, twitter-writer, email-writer]`. The writers run concurrently after the strategist completes.

---

### newsletter-engine

**Goal**: Build and monetize a newsletter through systematic testing.

**Flow**: `curator -> writer -> growth-hacker`

**Schedule**: Weekdays 6am | **Budget**: $20/mo

**What it does**: The curator finds content worth sharing. The writer produces newsletter issues. The growth hacker tests subject lines, send times, monetization formats, and growth tactics.

**Experiment patterns**: Subject line A/B, content density, monetization placement, growth loop mechanics, send time optimization.

**Metrics**: Revenue per subscriber, open rate, click rate, subscriber growth rate.

---

### faceless-factory

**Goal**: Produce high-retention faceless short-form videos at scale.

**Flow**: `script-writer -> thumbnail-designer -> analytics`

**Schedule**: Weekdays 7am | **Budget**: $25/mo

**What it does**: Produces TikTok/YouTube Shorts scripts with retention optimization. The script writer generates hook-first scripts with real data. The thumbnail designer creates click-worthy frames. The analytics agent tracks AVD and CTR.

**Experiment patterns**: Hook format A/B, voice style, visual approach, length optimization (30s vs 60s vs 90s), niche crossover, posting cadence, platform split.

**Metrics**: Average view duration (target >50%), CTR (target >5%), RPM by niche.

---

### ugc-factory

**Goal**: Produce AI-generated UGC-style ad content at $2-20/video that performs within 80% of human creator ROAS.

**Flow**: `script-writer -> reviewer -> performance-tracker`

**Schedule**: Weekdays 10am | **Budget**: $25/mo

**What it does**: Generates user-generated-content-style ad scripts. The script writer produces authentic-feeling ad scripts. The reviewer checks for UGC authenticity. The performance tracker evaluates against ROAS benchmarks.

---

### competitive-intel

**Goal**: Know what competitors ship before their customers do.

**Flow**: `scanner -> analyst -> briefer`

**Schedule**: Weekdays 7am | **Budget**: $20/mo

**What it does**: The scanner monitors competitor activity (product changes, content, hiring, pricing). The analyst identifies patterns and threats. The briefer produces actionable intelligence summaries.

---

### community-engine

**Goal**: Build and grow engaged communities with measurable DAU/MAU >20%.

**Flow**: `engagement-manager -> content-curator -> analyst`

**Schedule**: Daily 9am | **Budget**: $20/mo

**What it does**: The engagement manager designs community interactions and gamification. The content curator seeds discussions. The analyst tracks engagement metrics and identifies growth levers.

**Experiment patterns**: Gamification mechanics, quest design, cross-platform loops, content seeding strategies, moderation approaches.

---

## Customizing a Squad

### Edit team.yaml

The `team.yaml` file defines the squad's identity:

```yaml
name: Hook Lab
goal: find the message angles that make people stop scrolling.
flow: "researcher -> copywriter -> judge"
schedule: "0 8 * * 1-5"   # cron format. empty = manual only
budget_monthly: 30.0
tools: []                  # tools available to all agents in this team
```

Change the `goal` to match your specific context. Adjust the `schedule` or remove it for manual-only execution.

### Edit agent configs

Each agent has a YAML file in `agents/`:

```yaml
id: copywriter
name: Hook Writer
model:
  max_tokens: 800
  temperature: 0.7
instructions: |
  you write hooks. not posts, not articles...
metric:
  name: hook_score
  target: 8.5
  measurement_window_hours: 24
experiment_config:
  min_sample_size: 5
  auto_propose: true
```

Key fields to customize:

- **instructions**: The agent's system prompt. This is where you define behavior, rules, and output format.
- **model.max_tokens**: Cap output length. Lower = cheaper.
- **model.temperature**: 0.2 for analytical agents, 0.7 for creative agents.
- **metric.name**: What the agent optimizes for. Must be measurable (by self-eval or external metric).
- **metric.target**: The score that counts as success.
- **experiment_config.min_sample_size**: How many runs before issuing a verdict. Lower = faster iteration, higher = more confidence.
- **experiment_config.auto_propose**: If true, the agent automatically creates new experiments after closing one.

Model selection is handled by OpenRouter. You can set a specific `model_id` or leave it blank to use the routing config from `config.yaml`.

### Edit program.md

The `program.md` file is the squad's playbook. It contains:

- **Mission**: What this squad does and why
- **How growth teams actually do this**: Real-world context so the agents have domain knowledge
- **Experiment patterns**: Specific experiments the squad should run
- **Metrics**: Primary (self-eval) and production (external) metrics
- **Constraints**: Rules that prevent bad output

This file is injected into every agent's system prompt as "Team Program". Edit it to add your industry context, specific competitors, or custom experiment ideas.

### Edit strategy.md

The `strategy.md` file is in `agents/` (or `results/{agent_id}/` after first run). It starts with seed knowledge: validated patterns from real growth data. The experiment loop appends to this file automatically.

The seed knowledge is not gospel. It's a starting hypothesis. The experiment loop will keep what works and discard what doesn't for your specific audience.

You can manually edit `strategy.md` to:

- Add patterns you've already validated outside swarma
- Remove patterns that don't apply to your context
- Adjust baselines based on your actual metrics

## Creating a Squad from Scratch

### Option 1: Manual creation

```bash
swarma team create my-squad
```

This prompts for goal and flow, then creates agent stubs. Fill in the agent instructions and you're running.

### Option 2: AI-generated from a goal

```bash
swarma team create my-squad \
  --from-goal "improve email open rates for our SaaS onboarding sequence" \
  --context "developer tools, 500 new signups/week, current open rate 22%" \
  --budget 25
```

The generator designs agents, picks models, writes instructions, creates a program and strategy, and proposes the first experiment. Review the output in `~/.swarma/instances/default/teams/my-squad/` before running.

### Option 3: Fork an existing squad

Copy a template and modify:

```bash
cp -r examples/cold-outbound ~/.swarma/instances/default/teams/sales-outbound
```

Edit `team.yaml` to change the name and goal. Edit agent instructions to match your sales context. Edit `program.md` to add your ICP, product details, and objection patterns.

### Squad structure

A complete squad directory:

```
my-squad/
  team.yaml          # name, goal, flow, schedule, budget
  program.md         # team knowledge, experiment patterns, constraints
  agents/
    agent-1.yaml     # config, instructions, metric, experiment config
    agent-2.yaml
    agent-3.yaml
    strategy.md      # shared seed knowledge (optional, per-agent after first run)
```

The minimum viable squad is `team.yaml` + one agent YAML. Everything else is optional but makes the squad smarter from cycle one.
