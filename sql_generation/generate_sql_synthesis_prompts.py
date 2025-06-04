import json
import random
import os
import pickle
import numpy as np
from pathlib import Path
from tqdm import tqdm

from prompt_templates.schema_ddl import prefixed_table_names, create_statements
from prompt_templates.sql_templates import complexity2criterion
from db_value_sampling import db_value_sampling

# ----- 기본 설정 -----
random.seed(42)

# 1. schema_ddl.py 불러오기
table_names, create_statements = prefixed_table_names, create_statements

# 2. prompt 템플릿 및 함수 정의 불러오기
prompt_template = open("./prompt_templates/sql_synthesis_prompt.txt", "r", encoding="utf-8").read()
functions = json.load(open("./prompt_templates/postgresql_funcs.json"))

sample_row_template = '''
Below are several sample rows for each table. Use these to help generate predicates (i.e., `WHERE` clauses) in your SQL query:

{sample_rows}
'''

sql_func_template = '''
### SQL Functions
You may consider one or more of the following SQL functions while generating the query:
{sql_funcs}
Important tips:
Except for the functions listed above, you may use any other functions as long as they conform to the syntax of the database engine.
'''

complexity_weights = [0.15, 0.25, 0.3, 0.3]

# 3. 프롬프트 생성
prompts = []
for i in tqdm(range(50)):  # 원하는 쿼리 수
    complexity = random.choices(["Simple", "Moderate", "Complex", "Highly Complex"], weights=complexity_weights, k=1)[0]
    complexity2n = {
        "Simple": 0,
        "Moderate": 1,
        "Complex": 2,
        "Highly Complex": 3,
    }

    # DB value 샘플링
    all_tables_data = db_value_sampling()

    sample_rows = []
    for table_name, df in all_tables_data.items():
        if len(df) == 0:
            continue
        # n_rows = np.random.choice([1, 2])
        n_rows = 1
        sample_df = df.sample(n=min(n_rows, len(df)))
        for _, row in sample_df.iterrows():
            row_str = ', '.join(f"{col}={repr(val)}" for col, val in row.items())
            sample_rows.append(f"-- {table_name}: {row_str}")

    db_value_prompt = sample_row_template.format(sample_rows="\n\n".join(sample_rows))

    # SQL 함수 샘플링
    function_num = random.randint(0, 2)
    if function_num == 0:
        sql_function_prompt = "### SQL Functions\nYou can use any function supported by the database engine."
    else:
        sql_funcs = ""
        sampled_functions = random.sample(functions, function_num)
        for idx, func in enumerate(sampled_functions):
            sql_funcs += f"Function {idx + 1}:\n" + func.strip() + "\n"
        sql_function_prompt = sql_func_template.format(sql_funcs=sql_funcs)

    column_count = np.random.geometric(0.7, 1)[0] + complexity2n[complexity]

    prompt = prompt_template.format(
        schema_str="\n\n".join(create_statements),
        sql_function_prompt=sql_function_prompt.strip(),
        db_value_prompt=db_value_prompt.strip(),
        complexity=complexity,
        criterion=complexity2criterion[complexity].strip(),
        db_engine="PostgreSQL",
        column_count=column_count
    )

    prompts.append({"complexity": complexity, "prompt": prompt, "db_id": "custom_schema"})

# 4. 저장
Path("prompts").mkdir(parents=True, exist_ok=True)
with open("prompts/sql_synthesis_prompts.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(prompts, indent=2, ensure_ascii=False))
print("✅ prompts/sql_synthesis_prompts.json 에 저장 완료")
