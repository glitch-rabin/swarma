# Programmatic SEO

## Mission

Generate thousands of pages from structured data + templates, targeting long-tail search queries. Each page must serve a specific user intent with real data. Quality gate is non-negotiable -- thin content gets the entire domain penalized.

## How This Actually Works in 2026

The proven model: Tripadvisor (75M+ pages, 226M+ visits/month), Zapier (2.6M+ pages, 16.2M visits/month), Wise (millions of currency pair pages). The pattern: structured dataset + page template + AI-generated analysis + internal linking + quality checks.

Two approaches:
- **Pro route**: Python/Node.js scripts. Full control. Best for >10K pages.
- **No-code route**: Airtable (data) + Webflow (CMS) + Whalesync (sync) + Byword/Sight AI (content). Good for 100-5K pages.

Key 2026 insight: AI can generate content but it cannot generate proprietary data. The data is the moat.

## Experiment Patterns

1. **Template depth**: minimal (title + data table + FAQ) vs rich (intro + analysis + comparison + FAQ) -- measure indexing rate
2. **Content enrichment**: data-only vs data + AI analysis vs data + expert quotes -- measure ranking velocity
3. **Internal linking density**: 3 vs 10 vs 20 internal links per page -- measure crawl efficiency
4. **Update frequency**: static vs quarterly vs monthly refresh -- measure ranking retention
5. **Page type**: comparison vs listicle vs how-to -- measure traffic per page type
6. **Schema markup**: with vs without structured data -- measure rich snippet appearance rate
7. **Indexing strategy**: submit all at once vs batch 100/week -- measure index rate

## Metrics

- **Primary**: indexed_pages (target: >80% of generated pages indexed by Google)
- **Traffic**: organic_traffic_per_page, traffic_per_cluster
- **Quality**: content_quality_score (automated thin-content detection)
- **Revenue**: revenue_per_page (for commercial intent pages)
- **Technical**: crawl_budget_utilization, keyword_rankings

## Constraints

- Every page must contain proprietary or curated data that AI did not invent
- Kill pages with zero traffic after 90 days
- E-E-A-T signals on every page: author attribution, data sources cited, last-updated dates
- Internal linking structure must be planned before publishing (not bolted on after)
- No page goes live without passing automated thin-content check
