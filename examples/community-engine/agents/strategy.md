# Community Engine Strategy

## Seed Knowledge (pre-experiment baseline)

Data from 2026 growth ops landscape research. Community-led growth is the highest-retention, lowest-CAC channel -- when the engagement loops work.

### XP/Quest Gamification System

Members earn XP for valuable actions:
- Messages in channels: 1-5 XP (weighted by channel relevance)
- Reactions given/received: 1 XP
- Quest completion: 10-100 XP (varies by difficulty)
- Event attendance: 25 XP
- Content creation (guides, tutorials): 50-200 XP
- Referrals: 100 XP per verified referral

Levels unlock real value:
- Level 1-5: access to basic channels
- Level 5-10: exclusive discussion channels, early access to content
- Level 10-20: priority support, beta access, role badges
- Level 20+: ambassador program eligibility, direct access to team

### Quest System (Galxe/Zealy/GMFI Bot)

**On-chain quests** (Web3 communities):
- Token transactions, NFT minting, governance votes
- Verified via on-chain data (no self-reporting)
- Rewards: XP, exclusive NFTs, token allocations

**Off-chain quests** (any community):
- Social shares, content creation, bug reports, referrals
- Tweet about the project, create a tutorial, write a review
- Verified via API integrations (Twitter API, form submissions)
- Rewards: XP, roles, discounts, exclusive access

Quest completion rate benchmark: >30% for active quests. Below 20% = quest is too hard or reward is too weak.

### DAU/MAU Targets

| Health Level | DAU/MAU | What It Means |
|-------------|---------|---------------|
| Excellent | >30% | Habitual daily usage. Social media tier. |
| Healthy | 20-30% | Strong engagement. Most successful communities. |
| Moderate | 10-20% | Growing but not sticky. Need better loops. |
| Struggling | <10% | Ghost town risk. Intervention needed. |

Target: >20% DAU/MAU. Achieve through daily check-in rewards, streak mechanics, and regular programming (AMAs, challenges, discussions).

### UGC Amplification

The highest-value community content is member-created:
- Tutorials, guides, and how-tos
- Bug reports and feature requests
- Success stories and case studies
- Memes and cultural content

Amplification loop: member creates content -> community team highlights it -> member gets XP/recognition -> more members create content. This creates a flywheel that reduces content production load.

### Ambassador Programs

Power users (top 5% by XP and quality) become ambassadors:
- Responsibilities: moderate, welcome new members, create content, represent in external channels
- Rewards: direct team access, exclusive merch, revenue share, token allocation
- Selection: earned (not applied for). Based on XP + quality metrics over 90 days.
- Structure: tiered (Junior -> Senior -> Lead Ambassador). Each tier = more access + more responsibility.

### Cross-Platform Integration

Twitter -> Discord trigger examples:
- Tweet mentioning project -> XP reward in Discord
- Retweet announcement -> quest completion
- Thread about project -> featured in community channel

Telegram -> Discord:
- Telegram activity feeds Discord leaderboard
- Unified identity across both platforms
- Cross-promotion quests (join both = bonus XP)

### Onboarding Automation

New member joins -> automated flow:
1. Welcome DM with community guide (personalized by how they joined)
2. Reaction role selection (self-assign interests -> routed to relevant channels)
3. First quest: introduce yourself (low barrier, immediate XP reward)
4. Day 3: check-in DM (are they finding value? need help?)
5. Day 7: streak challenge invitation

Personalized onboarding increases engagement by 40% vs dump-them-in-general approach.

### Tools Stack

| Layer | Tool | Notes |
|-------|------|-------|
| XP/Leveling | MEE6, Arcane, Tatsu | Auto XP tracking, role unlocks, leaderboards |
| Quests | Galxe, Zealy, GMFI Bot | On-chain + off-chain tasks |
| Token gating | Collab.land | NFT/token-based channel access |
| Moderation | MEE6, Wick, Dyno | Anti-spam, anti-raid, auto-moderation |
| Telegram gamification | Growthly, GMFI Bot | Web2 + Web3 activity bridge |
| Analytics | Statbot, CommunityOne | Community health metrics |
| Funnel automation | ManyChat, custom bots | Lead capture and nurture |

### Patterns to Test

- [ ] Onboarding: instant access vs guided tour vs quiz routing -- D7 retention
- [ ] XP decay: does losing XP for inactivity drive re-engagement or accelerate churn?
- [ ] Quest reward types: XP vs NFT vs discount vs access -- completion rate
- [ ] Streak mechanics: daily vs weekly cadence -- DAU consistency
- [ ] Channel architecture: broad vs niche -- message quality and volume
- [ ] Cross-platform quests: combined vs single-platform -- growth rate
- [ ] Token gating: low barrier (1 token) vs high (100 tokens) -- conversion and quality

### Anti-Patterns

- "gm" culture without substance (inflates message count, doesn't build value)
- XP systems that reward quantity over quality (spam farming)
- No moderation infrastructure (one bot raid = community dies)
- Over-gamification (members feel manipulated, not engaged)
- Token gating too high (kills growth) or too low (no signal)
- Ambassador programs without clear criteria (political, not meritocratic)
- Ignoring retention curves (most drop-off at D1 and D7 -- fix onboarding first)
