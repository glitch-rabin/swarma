# Retention Squad

## Mission

Reduce churn and increase engagement through systematic retention experiments. Find the signals that predict churn, the interventions that prevent it, and the re-engagement patterns that bring users back.

## How Growth Teams Actually Do This

Retention is the multiplier on everything else. A 5% improvement in retention compounds harder than a 5% improvement in acquisition.

Real retention work:

- **Churn signal identification**: what behaviors predict someone leaving? (login frequency drop, feature usage decline, support ticket volume)
- **Intervention timing**: when is the right moment to reach out? too early = annoying, too late = gone
- **Win-back messaging**: what brings churned users back? discount? new feature? "we miss you"?
- **Engagement hooks**: what makes users come back daily/weekly without prompting?
- **Habit formation**: can you build a natural loop that makes the product part of someone's routine?

## Experiment Patterns

1. **Churn prediction signals** -- which behavioral change best predicts churn? test: login frequency vs feature usage vs session duration
2. **Intervention timing** -- reach out at 3 days inactive vs 7 days vs 14 days. earlier = more responsive but higher false positive rate.
3. **Win-back angle** -- "we shipped X you asked for" vs "here's what you're missing" vs discount offer vs personal note
4. **Re-engagement channel** -- email vs in-app notification vs SMS vs push. which channel has the highest re-activation rate?
5. **Feature discovery nudges** -- users who find feature X retain 2x. how do you get more users to feature X?
6. **Habit loop design** -- daily digest vs weekly summary vs triggered alerts. which creates a routine?

## Metrics

- **Primary**: reactivation_quality (self-eval on relevance + timing + tone + actionability)
- **Production**: churn_rate, reactivation_rate, time_to_churn, DAU/MAU ratio via webhook
- **Signal**: high email open rate + low reactivation = the message is interesting but doesn't drive action. the email needs a bridge to the product, not just information.

## Constraints

- Respect the user. "we miss you" is fine. "last chance!!!" is not.
- Personalization is not optional. generic win-back emails are spam.
- Measure reactivation (user comes back AND does something), not just email opens.
- Every experiment must have a clear control group of users who got no intervention.
