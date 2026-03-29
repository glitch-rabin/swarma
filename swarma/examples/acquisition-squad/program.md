# Acquisition Squad

## Mission

Build multi-agent outbound acquisition pipelines. Prospect identification, data enrichment, personalized multi-channel outreach (email + LinkedIn + phone), follow-up sequencing, and meeting booking. Not cold email blasts -- full-funnel orchestration with real-time adaptation based on engagement signals.

## How This Actually Works in 2026

The pipeline: ICP definition -> AI prospect identification (LinkedIn, Crunchbase, job boards, funding announcements) -> Clay enrichment (50+ data providers) -> AI scoring by fit + timing -> personalized message generation (not mail-merge) -> multi-channel orchestration (LinkedIn Day 1, Email Day 3, follow-up Day 7, engagement touch Day 10, final Day 14) -> AI response classification -> meeting booking.

Numbers: AI-driven lead qualification delivers -30% CAC, +15% revenue. Multi-agent systems outperform single-agent by 90% on complex tasks. Landbase claims 4-7x conversion rate improvement, 70-80% cost savings vs traditional SDR teams.

## Experiment Patterns

1. **Channel sequencing**: email-first vs LinkedIn-first vs phone-first -- measure reply rate
2. **Personalization depth**: role-based vs company-research vs post-reference -- measure positive reply rate
3. **Timing**: Monday AM vs Wednesday PM vs Friday -- measure open rate by day/time
4. **Signal-based triggers**: outreach after funding vs job posting vs content publication
5. **Human-in-the-loop vs full-auto**: AI handles all vs AI + human review before send -- measure quality
6. **Sequence length**: 3-step vs 5-step vs 7-step -- measure diminishing returns

## Metrics

- **Primary**: positive_reply_rate (target: >2%)
- **Volume**: reply_rate (target: >5%), meeting_booked_rate (target: >1%)
- **Efficiency**: CAC, pipeline_generated_value
- **Sequence**: completion_rate (% who receive full sequence without bouncing)
- **Attribution**: channel_attribution (which channel drives most conversions)

## Constraints

- Every outreach message must reference something specific to the prospect (not mail-merge)
- Respect platform limits: LinkedIn connection request limits, email warmup requirements
- Signal-based timing: outreach triggered by intent signals, not arbitrary cadence
- Adapt in real-time: if prospect engages on LinkedIn, deprioritize email channel
- Response classification must route interested replies to human within 1 hour
