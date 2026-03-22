# Activation Flow

## Mission

Optimize the path from signup to first value moment. Test onboarding sequences, welcome flows, and activation nudges to find what gets users to "aha" fastest.

## How Growth Teams Actually Do This

Activation is where most products leak users. The gap between "signed up" and "got value" is where experiments have the highest ROI.

Real activation experiments:

- **Time-to-value reduction**: how many steps between signup and first success? cut one.
- **Welcome sequence testing**: what order do you introduce features? what do you skip?
- **Aha moment identification**: which action most predicts retention? push users toward it.
- **Friction audit**: every form field, every extra click, every "complete your profile" -- does it help or hurt?
- **Social proof timing**: when do you show "1,000 teams use this" -- signup page or post-signup?

## Experiment Patterns

1. **Sequence length** -- 3-email welcome vs 5-email vs 7-email. measure activation rate, not open rate.
2. **Value-first vs setup-first** -- show the product working immediately vs "complete your profile first"
3. **Guided vs self-serve** -- wizard walkthrough vs "here's the dashboard, explore"
4. **Social proof placement** -- pre-signup vs post-signup vs after first success
5. **Empty state design** -- blank dashboard vs pre-populated with sample data vs guided first task
6. **Nudge timing** -- immediate followup vs 24h vs 48h for users who signed up but didn't activate

## Metrics

- **Primary**: activation_quality (self-eval on clarity + motivation + friction reduction)
- **Production**: activation_rate, time_to_first_value, drop_off_by_step via webhook
- **Signal**: high email open rate + low activation = the emails are interesting but don't drive action. fix the CTA, not the content.

## Constraints

- Every experiment must target a specific step in the activation funnel.
- Reduce friction before adding motivation. most activation problems are UX problems, not messaging problems.
- Measure activation, not engagement. a user who completes setup once is worth more than one who opens 5 emails.
