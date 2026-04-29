## Reflection and Ethics

### Limitations and Biases

For limitations of this project, the recommendations are limited by my current dataset in `data/cleanedClassicHits.csv`, may not fully represent all genres, eras, or artists. Furthermore,since the LLM recommends based on prompts, any vague prompts may result in weird or unfitting outputs. 

### Potential Misuse and Prevention

Potential misuse is people trusting the LLM output as the objective "best match" when they are simply probabilistic suggestions. People might also view the LLM's generated explanations as pure fact without factchecking. These were prevented by showing other top retrieved candidates alongside the top choice for transparency, as well as being clear to the user what the AI is logically processing.

### What Surprised Me During Reliability Testing

The biggest surprise to me was how often systems can seem functional when they actually don't work in reality.Before creating strict validation, the fallback logic produced convincing yet false outputs even when NIM failed, which made issues hard to detect. Forcing explicit errors in my code made failures obvious and easier to fix.

### Collaboration with AI During This Project

AI guided me a ton in this project through the system design and implementation. A helpful suggestion was splitting combined follow-up prompts into separate questions to make the user experience better. An incorrect sugestion was when it attempted to implement a fallback behavior in my code when the goal was to purely rely on the NIM LLM, creating confusing outputs.

