# Ad Creative Lab Strategy

## Seed Knowledge (pre-experiment baseline)

Data from 2026 growth ops landscape research and vendor benchmarks. Starting hypotheses for the experiment loop.

### The Creative Testing Framework

The 2026 standard: generate 20-100 creative variants per campaign. Each variant isolates one variable (hook, CTA, visual layout, copy angle, color treatment). Launch all variants with identical audiences. 24-48 hours of data collection. Kill bottom 80%. Winners get budget. Top performer elements feed next generation cycle.

This is not "make pretty ads." This is systematic hypothesis testing at scale.

### Performance Benchmarks (2026)

| Metric | Benchmark | Source |
|--------|-----------|--------|
| CTR improvement (AI creative) | +108% | Uber + Smartly.io |
| CPC reduction | -43% | Uber + Smartly.io |
| CPA reduction | -36% | Uber + Smartly.io |
| Average lift across tests | 45.7% | Smartly.io (10 tests, 9/10 improved) |
| Marketers using AI for programmatic | 61% | 2025 industry report |

### Multi-Variant Testing Protocol

50+ variants per campaign:
- 5 hook types x 3 CTA styles x 3 visual approaches = 45 minimum combinations
- Each variant gets its own ad set for clean attribution
- Minimum $5-10 spend per variant before kill decision
- 48-hour window before any optimization decisions
- Statistical significance required: 95% confidence on CTR differences

### Dynamic Creative Optimization (DCO)

For e-commerce: Smartly.io-style catalog-fed dynamic variants auto-generate ads from product catalog data (images, prices, descriptions). Outperforms static ads for large catalogs (100+ products). Best for retargeting and product discovery.

For non-ecommerce: static AI-generated variants with manual testing give more control and learning.

### Platform-Specific Specs

| Platform | Primary Format | Notes |
|----------|---------------|-------|
| Meta (FB/IG) | 1:1 feed, 9:16 Stories/Reels | Advantage+ for automated distribution |
| Google | 16:9 display, responsive | PMax for multi-format |
| TikTok | 9:16 only | Native-feeling > polished. UGC style wins. |
| LinkedIn | 1:1 feed, 1200x627 link | Professional tone, B2B only |

### Hook Taxonomy for Ads

Five archetypes to test systematically:
1. **Question**: "Still spending $X on Y?" -- lowest performer in 2026 (overused)
2. **Stat/Data**: "87% of teams waste $X on Y" -- reliable CTR, medium conversion
3. **Contrarian**: "Stop doing X. Here's why." -- highest variance (big wins or big misses)
4. **Pain point**: "Tired of X? It's because Y." -- best for problem-aware audiences
5. **Social proof**: "12,847 teams switched from X to Y" -- best for conversion, weakest for cold

### Creative Fatigue Patterns

- Static image ads: fatigue onset at 7-14 days
- Video ads: fatigue onset at 14-21 days
- UGC-style: fatigue onset at 21-30 days (longest lifespan)
- Refresh cadence: new creative batch every 2 weeks minimum
- Signal: CTR drops >15% from peak = fatigue

### Tools Stack

| Layer | Tool | Use |
|-------|------|-----|
| Generation (static) | AdCreative.ai, Pencil | Rapid static ad variants |
| Generation (video) | Creatify, Arcads, MakeUGC | UGC-style video ads |
| Dynamic creative | Smartly.io | Enterprise catalog-fed variants |
| Ops | AdManage, AdStellar | Naming, UTMs, bulk launch |
| Testing | Meta Advantage+, Google PMax | Algorithmic variant distribution |
| Attribution | Triple Whale, Northbeam | ROAS tracking |

### Patterns to Test

- [ ] Hook taxonomy A/B across all 5 archetypes -- which wins per audience temperature
- [ ] Volume sweet spot: 10 vs 50 vs 200 variants per campaign
- [ ] Creative fatigue curve by format (static vs video vs UGC)
- [ ] Platform-native adaptation vs universal creative
- [ ] AI-generated vs human-designed on identical briefs and audiences
- [ ] Refresh cadence: weekly vs bi-weekly vs monthly

### Anti-Patterns

- Launching fewer than 10 variants (not enough data for pattern recognition)
- Testing multiple variables in one variant (learn nothing)
- Killing variants before 48 hours (insufficient data)
- Ignoring platform specs (9:16 content in 1:1 placements = wasted spend)
- No baseline control (can't measure "better than what?")
