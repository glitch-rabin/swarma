# Cost Optimizer Team

## Mission
Continuously reduce the cost of running all agent teams without degrading output quality. This means finding shorter prompts that produce equivalent results, cheaper models for tasks that don't need expensive ones, and routing strategies that use premium models only when the task requires it.

## How It Works
The tester takes existing agent prompts and produces optimized variants: shorter system prompts, lower max_tokens settings, cheaper model substitutions, and two-stage routing (cheap model tries first, expensive model handles failures). The analyst evaluates whether the optimized versions maintain quality by running side-by-side comparisons.

## Constraints
- Quality floor: optimized versions must score within 0.5 points of the original on the team's primary metric.
- Test each optimization independently. Don't stack multiple changes -- isolate what works.
- Always measure cost reduction as a percentage, not absolute dollars.
- Track cumulative monthly savings across all optimizations.
- Never sacrifice reliability (failure rate) for cost. A prompt that's 50% cheaper but fails 10% of the time is worse.
