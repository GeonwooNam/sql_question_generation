# Stylized Natural Language Question Synthesis

This is the second step in our data generation framework, dedicated to generating **stylistically diverse** natural language questions from synthetic SQL queries.

Unlike conventional question generation, this module enables **fine-grained control over linguistic style**, allowing the system to simulate various user interaction patterns:

- **Stylistic variation**: Questions can be generated in styles such as *Formal*, *Colloquial*, *Imperative*, *Interrogative*, *Descriptive*, *Concise*, *Vague*, *Metaphorical*, and *Multi-turn Dialogue*.
- **External knowledge injection**: For *Vague* and *Metaphorical* styles, the system supports incorporating domain knowledge or inferred context.
- **Dialogue formatting**: The *Multi-turn Dialogue* style generates multi-turn conversations to emulate real-time user–assistant exchanges.

These settings allow for high-quality, human-like questions tailored for training and evaluating text-to-SQL systems under diverse linguistic conditions.

---

## Step 1: Question Generation

Generate stylized natural language questions from synthetic SQL queries.

1. Run `python3 generate_question_synthesis_prompts.py` to create prompts for stylized question generation.
2. Execute `python3 synthesize_question.py` to generate natural language questions from the prompts.
   - Implement the `llm_inference()` function to connect your preferred LLM backend.
   - Each prompt is sampled at a temperature of `0.8` to encourage stylistic diversity.
   - Post-processing is included within this step to ensure semantic alignment between the question and the SQL intent.

The final `<question, SQL>` pairs (with question style & SQL complexity written) will be saved to `./results/synthetic_questions.jsonl`.
