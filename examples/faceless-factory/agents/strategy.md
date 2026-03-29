# Faceless Factory Strategy

## Seed Knowledge (pre-experiment baseline)

Data from 2026 growth ops landscape research. Starting hypotheses -- the experiment loop validates or discards.

### Production Pipeline (validated stack)

Google Sheets (topics) -> OpenAI/Claude (script) -> ElevenLabs (voice) -> Leonardo AI/Flux (images) -> Creatomate/Shotstack (assembly) -> YouTube/TikTok API (publish). Full pipeline on n8n cron. Zero human touch per video.

Cost breakdown:
- Orchestration: $0-50/mo (n8n self-hosted)
- Script: $0.01-0.10/script
- Voice: $5-99/mo (ElevenLabs)
- Images: $10-60/mo (Leonardo AI, Flux)
- Video assembly: $20-100/mo (Creatomate, Shotstack)
- Publishing: $0 (platform APIs)
- Total: $35-310/mo for unlimited volume

### Retention Curve Optimization

- First 3 seconds = hook. This is the only frame that matters for initial distribution.
- AVD >50% = YouTube promotes to Browse/Suggested. Below 50% = dead.
- Retention dips at seconds 8-12 in most Shorts. Insert a visual pattern break or re-hook here.
- End screens on Shorts don't work. CTA must be verbal, embedded in final 5 seconds.
- Loop endings (where the end connects to the start) boost rewatch rate on TikTok.

### Hook-First Scripting Patterns

From analysis of top-performing faceless channels:
- **Shocking stat opener**: "87% of people do X wrong" -- highest CTR, medium AVD
- **Contrarian claim**: "Everything you know about X is backwards" -- high CTR, high variance
- **Story micro-scene**: "At 3am last Tuesday, this happened" -- medium CTR, highest AVD
- **List tease**: "3 things about X that nobody talks about" -- reliable CTR, reliable AVD
- The question hook ("Did you know...?") is the most overused and lowest-performing format in 2026.

### Niche RPM Data

| Niche | CPM Range | Production Notes |
|-------|-----------|-----------------|
| Personal Finance | $12-20 | Highest-paying. Competitive. Needs real data differentiation. |
| Tech/AI Tools | $8-15 | Good for affiliate stacking. Demo-style content works. |
| True Crime | $6-12 | High retention, long watch time. AI narration is standard. |
| Education/Facts | $4-8 | Massive volume potential. Lowest bar but also lowest CPM. |
| Scary Stories | $4-8 | High engagement, cheap to produce. Voiceover is everything. |

### Batch Production Protocol

30+ videos/week requires:
- Topic queue pre-loaded 2 weeks ahead (50+ topics minimum in buffer)
- Scripts generated in batches of 10, reviewed together for variety
- Visual assets generated in parallel (not sequential per video)
- Assembly and publishing fully automated via API
- Performance review weekly: kill bottom 20% topics, double down on top performers

### Trending Audio Patterns

- TikTok: trending audio = 30-50% distribution boost in first 24 hours
- YouTube Shorts: original audio performs equally to trending (YouTube prioritizes watch time over audio trends)
- Strategy: use trending audio for TikTok versions, original consistent voice for YouTube

### Critical Risk: Content Policy (2026)

YouTube suspended thousands of faceless AI channels in early 2026. The surviving channels share these traits:
- Genuine research or curated data (not just AI-regurgitated facts)
- Unique angles or original analysis
- Consistent brand voice and visual identity
- Human editorial direction (even if production is fully automated)

The quality gate is non-negotiable. Volume without insight = channel death.

### Patterns to Test

- [ ] Hook format taxonomy across 5 archetypes -- which gets highest CTR per niche
- [ ] AI-generated visuals vs stock footage -- retention impact
- [ ] Voice clone consistency vs rotating stock voices -- subscriber conversion
- [ ] Cross-posting same content vs platform-native edits -- RPM per platform
- [ ] Posting time optimization: morning vs evening vs late night
- [ ] Niche mixing on single channel vs dedicated niche channels

### Anti-Patterns

- "Did you know?" hooks (overused, lowest CTR in 2026)
- Generic AI narration without personality or brand voice
- No data, no specifics, just "interesting facts" energy
- Publishing 3/day with no quality review (triggers YouTube's inauthentic content filter)
- Same visual template for every video (viewer fatigue within 2 weeks)
