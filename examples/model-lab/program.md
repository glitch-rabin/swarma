# Model Lab Team

## Mission
Systematically benchmark models across task types (writing, research, reasoning, routing, critique) to find the best quality-per-dollar option for each. New models drop weekly -- this team keeps the model roster current and catches when a cheaper model starts outperforming an expensive one.

## How It Works
The prompt engineer designs standardized test prompts for each task category, with clear scoring rubrics. The evaluator runs those prompts against candidate models, scores the outputs, and calculates quality-per-dollar ratios. Results feed back into team configurations across the whole system.

## Constraints
- Every benchmark needs a minimum sample size of 5 runs per model (variance matters).
- Score on task-specific criteria, not vibes. A writing benchmark scores on hook quality, specificity, and voice. A reasoning benchmark scores on logical validity and conclusion quality.
- Always include current production model as the baseline.
- Track cost per 1K tokens at the time of benchmark (prices change).
- Results must be reproducible: same prompt, same temperature, logged outputs.
