# Acquisition Squad Strategy

## Seed Knowledge (pre-experiment baseline)

Data from 2026 growth ops landscape research. Outbound acquisition has shifted from spray-and-pray to agent-orchestrated, signal-driven, multi-channel sequencing.

### Performance Benchmarks (2026)

| Metric | Benchmark | Notes |
|--------|-----------|-------|
| Reply rate (cold outbound) | >5% | Below 3% = messaging or targeting problem |
| Positive reply rate | >2% | Below 1% = wrong ICP or wrong angle |
| Meeting booked rate | >1% | From total prospects contacted |
| CAC reduction (AI vs manual) | -30% | Industry average |
| Revenue uplift (AI lead qual) | +15% | Industry average |
| Multi-agent vs single-agent | +90% performance | On complex orchestration tasks |
| Landbase conversion improvement | 4-7x | vs traditional SDR teams |
| Landbase cost savings | 70-80% | vs human SDR teams |

### Intent Signal Detection

Not all prospects are equal. Signal-based prioritization:

**Hot signals (outreach within 48 hours):**
- Series A/B funding announced (company is hiring and buying)
- Job posting for your target role (pain is active)
- Published content on your topic (awareness exists)
- Visited your website or engaged with your content

**Warm signals (outreach within 1 week):**
- Company headcount growing 20%+ YoY
- New executive hire in your target department
- Competitor mentioned in their content
- Industry event attendance

**Cold signals (lower priority, need more personalization):**
- Matches ICP but no active signals
- Stale company (no recent news)
- Already have incumbent solution

### Multi-Channel Sequencing Protocol

Standard 14-day sequence (adapt based on engagement):
- **Day 1**: LinkedIn connection request with personalized note (30 words max)
- **Day 3**: Email if no LinkedIn response (research-based personalization)
- **Day 7**: Follow-up email with different angle (not "just following up")
- **Day 10**: LinkedIn engagement touch (comment on their post, no pitch)
- **Day 14**: Final email with value-first CTA (resource, case study, insight)

Real-time adaptation rules:
- If prospect accepts LinkedIn connection -> skip email Day 3, send LinkedIn DM instead
- If prospect opens email but doesn't reply -> try different subject line angle
- If prospect clicks link in email -> advance to direct CTA
- If no engagement on any channel after full sequence -> archive for 90 days

### Personalization Depth Tiers

| Tier | What It Includes | Time/Prospect | Reply Rate Lift |
|------|-----------------|---------------|-----------------|
| T1 (role-based) | "As a [role] at a [stage] company..." | 30 seconds | Baseline |
| T2 (company-research) | + recent company news, funding, hiring | 2 minutes | +40-60% |
| T3 (post-reference) | + specific content they published/shared | 5 minutes | +80-120% |

T2 is the sweet spot for volume + quality. T3 for high-value targets only.

### Tools Stack

| Layer | Tool | What It Does |
|-------|------|-------------|
| Enrichment | Clay | 50+ data providers, AI enrichment, waterfall logic |
| Email infra | Instantly, Smartlead | Unlimited mailboxes, warmup, deliverability |
| Multi-channel | Smartlead (SmartAgents) | AI workflow automation |
| Full-stack GTM | Landbase | Autonomous AI SDR. GTM-1 Omni model, 40M+ campaigns |
| LinkedIn | Expandi, Dripify | LinkedIn sequences (use carefully -- bans) |
| Meeting booking | Calendly, Chili Piper | Auto-scheduling |
| CRM | HubSpot, Salesforce | Pipeline tracking |
| Orchestration | n8n, Make.com | Custom workflow stitching |

### Key Numbers from Landbase

- GTM-1 Omni model trained on 40M+ campaigns
- Claims: $100M+ pipeline generated across customer base
- 4-7x conversion rate improvement vs manual outbound
- 70-80% cost savings vs traditional SDR team
- Campaign optimization in 24-48 hours vs weeks for manual iteration

### Patterns to Test

- [ ] Channel sequencing order: email-first vs LinkedIn-first vs simultaneous
- [ ] Personalization depth: T1 vs T2 vs T3 -- reply rate vs time investment
- [ ] Timing optimization: day of week, time of day, timezone-adjusted
- [ ] Signal-based triggers: funding vs job posting vs content publication
- [ ] Sequence length: 3-touch vs 5-touch vs 7-touch
- [ ] Human-in-the-loop: AI sends all vs human reviews before send

### Anti-Patterns

- "Just following up" as follow-up message (adds zero value)
- Same message to every prospect (mail-merge is dead)
- Ignoring LinkedIn connection limits (account ban risk)
- No email warmup before campaign launch (deliverability disaster)
- Single-channel only (multi-channel outperforms single by 2-4x)
- No response classification (interested replies sitting unread = lost deals)
- Sequence that doesn't adapt to engagement signals (robotic, not intelligent)
