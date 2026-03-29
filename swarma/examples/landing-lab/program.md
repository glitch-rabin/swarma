# Landing Lab

## Mission

Optimize landing page copy and structure through systematic A/B experimentation. Find the headline, hero section, proof, and CTA combination that maximizes conversion.

## How Growth Teams Actually Do This

Landing pages are the most testable surface in your stack. Every element is a variable:

- **Headline testing**: benefit-led vs feature-led vs question vs social proof
- **Hero section**: demo/screenshot vs video vs illustration vs text-only
- **Proof hierarchy**: logos first vs metrics first vs testimonials first
- **CTA placement**: above fold only vs repeated vs sticky
- **Page length**: short (1 screen) vs medium (3-5 sections) vs long (full story)
- **Objection handling**: FAQ vs inline vs separate section vs none

## Experiment Patterns

1. **Headline formula** -- "do X without Y" vs "N teams use us to X" vs "the fastest way to X"
2. **Social proof type** -- logo bar vs metric ("10K users") vs testimonial quotes vs case study snippets
3. **CTA copy** -- "get started free" vs "see a demo" vs "try for 14 days" vs custom to offer
4. **Page structure** -- problem-solution-proof vs proof-feature-CTA vs story-based narrative
5. **Specificity level** -- generic value prop vs persona-specific ("for growth teams" vs "for SaaS")
6. **Urgency and scarcity** -- deadline vs limited spots vs "prices increase" vs none (clean)

## Metrics

- **Primary**: persuasion_score (self-eval on clarity + credibility + urgency + CTA strength)
- **Production**: page_conversion_rate, time_on_page, scroll_depth, CTA_clicks via webhook
- **Signal**: high time-on-page + low conversion = the page is interesting but the CTA doesn't land. high bounce + high conversion among remainers = the page filters well but the headline loses people.

## Constraints

- One variable per test. changing headline + CTA + layout = no learnings.
- Every landing page must pass the 5-second test: can someone explain what this does after 5 seconds?
- No dark patterns. urgency must be real or absent.
- The page should work without images (text-first, imagery enhances).
