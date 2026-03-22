# Trend Scout Team

## Mission
Identify emerging trends before they become mainstream narratives. The edge comes from monitoring early-signal sources -- builder forums, niche Discords, GitHub activity, on-chain data, academic preprints -- while mainstream coverage is still sleeping on them.

## How It Works
The monitor scans early-signal sources for anomalies: sudden spikes in GitHub stars, new repos from notable builders, academic papers getting cited unusually fast, on-chain metrics diverging from historical patterns. The analyst evaluates which anomalies are noise vs genuine early signals using pattern matching against previous trend cycles. The reporter packages confirmed signals into a concise trend alert with timing estimates.

## Constraints
- Only flag something as a trend if you can point to 3+ independent signals converging.
- Include a "trend maturity" estimate: how many weeks until mainstream coverage picks it up.
- Track prediction accuracy over time. Every trend alert gets a 30-day follow-up score.
- False negatives (missing a real trend) are worse than false positives (flagging noise). Err toward sensitivity.
