# Pricing Lab

## Mission

Experiment with pricing presentation, packaging, and positioning to maximize conversion and revenue per visitor. Not the price itself -- how you frame it.

## How Growth Teams Actually Do This

Pricing is the highest-leverage page most teams never test. A 10% improvement in pricing page conversion is worth more than doubling traffic.

Real pricing experiments:

- **Anchor pricing**: does showing an expensive tier make the mid-tier feel reasonable?
- **Default selection**: which plan is pre-selected? annual vs monthly default?
- **Feature gating**: which features gate which tier? what makes someone upgrade?
- **Social proof on pricing**: "most popular" badge, user counts per tier, logos
- **Pricing page copy**: feature list vs outcome list vs "who it's for" framing
- **Free tier strategy**: free trial vs freemium vs "book a demo"

## Experiment Patterns

1. **Anchor effect** -- 2 tiers vs 3 tiers vs 4 tiers. the expensive tier exists to make the target tier look reasonable.
2. **Annual vs monthly default** -- which is pre-selected? what's the annual discount? (15% vs 20% vs "2 months free")
3. **Feature framing** -- feature list vs benefit list vs "who it's for" personas
4. **Social proof type** -- "10,000 teams" vs specific logos vs "most popular" badge vs none
5. **CTA copy** -- "start free trial" vs "get started" vs "see it in action" vs "talk to sales"
6. **Reverse trial** -- full access for 14 days then downgrade vs limited access then upgrade

## Metrics

- **Primary**: conversion_likelihood (self-eval on clarity + value perception + urgency)
- **Production**: pricing_page_conversion, plan_distribution, ARPU, trial_to_paid via webhook
- **Signal**: high traffic + low conversion = the price isn't the problem, the presentation is. high conversion + low ARPU = you're leaving money on the table with packaging.

## Constraints

- Test presentation, not price. price changes need real revenue data.
- Every variation must be implementable as a page change, not a product change.
- The pricing page is a conversion page, not a feature page. lead with outcomes.
