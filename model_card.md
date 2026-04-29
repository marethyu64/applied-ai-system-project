## Reflection and Ethics

### Limitations and Biases

- Dataset bias: recommendations are limited by what exists in `data/cleanedClassicHits.csv` and may under-represent genres, eras, or artists.
- Prompt sensitivity: LLM interpretation can vary based on wording, which can cause unstable outputs for vague prompts.
- Constraint tension: strict year cutoffs can force lower-quality matches if the filtered candidate pool is small.

### Potential Misuse and Prevention

- Potential misuse:
  - Over-trusting outputs as objective "best" matches when they are probabilistic suggestions.
  - Using generated explanations as facts without verification.
- Mitigations in this project:
  - Show top retrieved candidates alongside the final choice for transparency.
  - Keep user-in-the-loop review as part of normal operation.
  - Fail fast on invalid key/invalid model output to avoid hidden degraded behavior.

### What Surprised Me During Reliability Testing

The biggest surprise was how often systems can appear functional while silently degrading quality. Before strict validation, fallback logic produced plausible outputs even when NIM failed, which made issues hard to detect. Enforcing explicit errors made failures obvious and easier to fix.

### Collaboration with AI During This Project

- Helpful AI suggestion:
  - Splitting combined follow-up prompts into separate mood and energy questions improved clarity and gave cleaner user inputs.
- Flawed/incorrect AI suggestion:
  - A previous suggestion left heuristic fallback behavior in place while the goal was "NIM-only." That mismatch caused confusing outputs and had to be corrected by removing fallback paths and adding strict error handling.


