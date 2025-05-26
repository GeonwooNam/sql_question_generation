# Complexity-Aware SQL Query Generation

This is the first step in our data generation framework, focused on generating complexity-aware SQL queries based on synthetic databases.
This module is responsible for generating SQL queries with varying levels of structural and logical complexity.  
Unlike naive SQL generation methods, this framework enables **fine-grained control** over:

- **Query complexity**: Queries are categorized as *Simple*, *Moderate*, *Complex*, or *Highly Complex*, each defined by distinct syntactic and semantic patterns (e.g., table joins, CTEs, subqueries, window functions).
- **Number of selected columns**: The number of columns in each generated query is dynamically determined based on its complexity, reflecting realistic query distributions.
- **SQL function usage**: Built-in support for sampling and injecting SQL functions (e.g., `CONCAT_WS`, `REPLACE`) for diversity and richness. You should include random n SQL functions in the query.

These settings allow for high-quality, diverse, and evaluable SQL queries tailored for downstream tasks such as question synthesis, model evaluation, and schema-based reasoning.


## Step 1: SQL Query Generation

Generate SQL queries by leveraging database schemas, database values, query complexity, and SQLite-supported functions.

1. Execute `python3 generate_sql_synthesis_prompts.py` to create prompts for SQL query generation.
2. Run `python3 synthesize_sql.py` to generate SQL queries using LLMs.
   - Implement the `llm_inference()` function to integrate your preferred LLM.
   - Post-processing is included in the file.
   - The final synthetic SQL queries will be saved in `./results/llm_results.jsonl`.
