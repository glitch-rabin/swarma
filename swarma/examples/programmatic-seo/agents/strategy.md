# Programmatic SEO Strategy

## Seed Knowledge (pre-experiment baseline)

Data from 2026 growth ops landscape research. Programmatic SEO is the highest-leverage content strategy when you have proprietary data. Without proprietary data, it's a spam factory.

### Who's Actually Winning (2026 numbers)

| Company | Pages | Monthly Organic Traffic | Strategy |
|---------|-------|------------------------|----------|
| Tripadvisor | 75M+ indexed | 226M+ visits/month | Location-specific attractions, reviews, bookings |
| Zapier | 2.6M+ | 16.2M visits/month | "{App 1} + {App 2} integrations" pages |
| Wise | Millions | Massive | Currency pair conversion pages with proprietary rate data |
| Nomadlist | Thousands | 50K/month | "Cost of living in {city}" with scraped data |
| Flyhomes | 10K -> 425K | Scaled fast | Real estate listings by neighborhood |

The pattern: every successful pSEO operation has a structured dataset that is either proprietary (Wise's rates), aggregated from multiple sources (Tripadvisor reviews), or derived from a unique combination (Zapier's integration matrix).

### Template + Data Variable Patterns

The keyword matrix formula: `{variable_1} + {variable_2} + {modifier}`
- "{product} vs {product}" -- comparison pages
- "{service} in {city}" -- location pages
- "best {category} for {use case}" -- listicle pages
- "{tool 1} + {tool 2} integration" -- combination pages

Each combination must produce a page with genuinely different content. If two pages look identical except for the city name, that's thin content.

### Topical Authority Clustering

Don't publish random pages. Build clusters:
1. **Hub page**: broad topic overview (e.g., "Email Marketing Tools")
2. **Spoke pages**: specific long-tail variations (e.g., "Mailchimp vs ConvertKit for SaaS")
3. **Internal links**: every spoke links to hub, hub links to top spokes, spokes cross-link to related spokes
4. **Publication order**: hub first, then spokes in batches of 10-20. Signals topical authority to Google.

### Internal Linking Architecture

Internal linking is the most underrated factor in pSEO:
- Every page needs 3-10 contextual internal links
- Link anchor text must be descriptive (not "click here")
- Hub pages should have 50+ inbound internal links
- Orphan pages (zero internal links) don't rank -- period
- Automated internal linking: use keyword mapping to auto-insert links in new pages

### Quality Thresholds (Non-Negotiable)

Google penalizes thin content at the domain level. One bad cluster can tank the entire site.

Quality gates before publishing any page:
1. **Unique content check**: >70% unique content per page (not just template filler)
2. **Data verification**: every data point traceable to source
3. **Word count minimum**: 300+ words of actual analysis (not counting template boilerplate)
4. **E-E-A-T signals**: author attribution, data source citation, last-updated date
5. **User intent match**: page must answer the specific query it targets
6. **No hallucinated data**: AI analysis only, never AI-invented data

Pages that fail any gate: do not publish. Fix or discard.

### Tools Stack

| Layer | Tool | Notes |
|-------|------|-------|
| Data | Airtable, PostgreSQL, Google Sheets | Structured data source |
| Content generation | Byword.ai | CSV -> bulk articles. GPT-5.4, Claude Opus 4.6, Gemini 3.1 Pro |
| Content generation | Sight AI | 13+ specialized AI agents, IndexNow integration |
| CMS | Webflow, WordPress, Next.js | Publishing layer |
| Sync | Whalesync | Airtable <-> Webflow sync |
| Audit | Screaming Frog, Ahrefs | Technical SEO audit |
| Indexing | IndexNow, Google Search Console API | Fast indexing |

### Patterns to Test

- [ ] Template depth: minimal vs rich -- indexing rate and traffic
- [ ] Content enrichment: data-only vs AI analysis vs expert quotes
- [ ] Internal linking density: 3 vs 10 vs 20 links per page
- [ ] Update frequency: static vs quarterly vs monthly refresh
- [ ] Schema markup impact on rich snippet appearance
- [ ] Indexing strategy: all at once vs batched 100/week
- [ ] Hub-first vs spoke-first publication order

### Anti-Patterns

- Publishing pages without proprietary data (pure AI-generated content = spam)
- No internal linking strategy (orphan pages never rank)
- Identical template with only variable swapped (thin content penalty)
- No quality gates (one bad cluster tanks the domain)
- Ignoring crawl budget (10K+ pages without sitemap management = wasted crawl budget)
- Publishing all pages at once (looks spammy to Google, batch in 100-200/week)
