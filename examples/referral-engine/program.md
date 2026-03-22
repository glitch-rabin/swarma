# Referral Engine

## Mission

Design and optimize viral loops and referral mechanics. Find the share trigger, incentive structure, and invitation flow that maximizes k-factor (viral coefficient).

## How Growth Teams Actually Do This

Referral is the cheapest acquisition channel when it works. Most referral programs fail because they incentivize the wrong action at the wrong time.

Real referral experiments:

- **Share trigger timing**: when in the user journey is someone most likely to refer? (after first success, after upgrade, after milestone)
- **Incentive structure**: two-sided (both get reward) vs one-sided (referrer only) vs altruistic ("give your friend $20")
- **Incentive type**: credit vs feature unlock vs cash vs status/badge
- **Invitation mechanic**: unique link vs invite code vs "share this" button vs direct integration (email, slack)
- **Social proof in referral**: "12 of your colleagues use this" vs generic invite

## Experiment Patterns

1. **Two-sided vs one-sided** -- "you both get $20" vs "get $20 for each friend." Dropbox, Uber, and Robinhood all used two-sided. test if it matters for your product.
2. **Share trigger timing** -- prompt after first success vs after 7 days vs after feature milestone. early = higher volume, late = higher quality referrals.
3. **Incentive magnitude** -- $10 vs $25 vs $50 credit. there's a ceiling where more money doesn't increase referrals.
4. **Mechanic friction** -- unique link (copy + paste) vs "enter their email" vs "connect your contacts." each has a conversion/quality tradeoff.
5. **Altruistic framing** -- "invite a friend" vs "give your friend X" vs "your team is incomplete." the frame changes who refers and why.
6. **Milestone referral** -- prompt after user hits a natural achievement. "you just saved 100 hours -- know anyone else who could?"

## Metrics

- **Primary**: referral_quality (self-eval on incentive clarity + share motivation + friction level)
- **Production**: k_factor, referral_conversion_rate, invites_per_user, referred_user_retention via webhook
- **Signal**: high invite rate + low conversion = the invitation isn't compelling for the invitee. fix the landing page, not the referral mechanic. high conversion + low retention of referred users = wrong audience is being referred.

## Constraints

- Referred users must retain at the same rate as organic users, or the channel is fake growth.
- No spam mechanics. invite-your-contacts-to-unlock is a dark pattern.
- Track referral quality, not just volume. 10 referrals that churn < 2 referrals that stay.
