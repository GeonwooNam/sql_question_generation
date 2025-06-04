from dotenv import load_dotenv
import os
import json
import time
from tqdm import tqdm

import pandas as pd
from sqlalchemy import create_engine, text

from prompt_templates.schema_ddl import table_names
from llm_api import GroqAPIClient
from synthesize_sql import extract_sql_query

import psycopg2
from psycopg2 import OperationalError


load_dotenv()  # .env 파일 불러오기

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# LLM 프롬프트 템플릿
LLM_PROMPT_TEMPLATE = """
The following SQL query has undergone several attempts to correct execution errors.
Please analyze the sequence of past queries and their error messages, and return a corrected SQL query that preserves the original intent.

Your goal is to fix:
- SQL syntax issues
- Schema or column name mismatches
- Invalid joins or aggregations
- NULL result handling (suggest COALESCE if needed)
    - if it is not aggregation column and has null value, try to erase it.

Focus on logical and schema-consistent corrections. Only return the corrected SQL.

Common Error Patterns to Fix:
1. **Missing Comma Example**
   - Bad: `SELECT id name FROM users`
   - Good: `SELECT id, name FROM users`

2. **Invalid Join Example**
   - Bad: `SELECT * FROM orders JOIN users ON user_id`
   - Good: `SELECT * FROM orders JOIN users ON orders.user_id = users.id`

3. **Aggregation Error Example**
   - Bad: `SELECT department, salary FROM employees GROUP BY department`
   - Good: `SELECT department, AVG(salary) FROM employees GROUP BY department`

4. column name error (Quoted identifiers)
    - Bad: late_fee_&_other_charges, state/province/city
    - Good: "late_fee_&_other_charges", b."state/province/city"
    
5. Erase annotations
    - Bad: WITH -- Calculate total receivable amount including VAT for each contract contract_receivable AS ( SELECT ...
    - Good: WITH contract_receivable AS ( SELECT ...
    - Bad: -- Calculate key performance indicators (KPIs) SELECT ci.contract_id, ci.loan_id, ...
    - Good: SELECT ci.contract_id, ci.loan_id, ...

[Query Correction History]
{history}

[Query Execution Result]
{row_result}

Output:
Corrected SQL only
"""


# 쿼리 실행 (LIMIT 1 추가)
def test_and_correct_sql_query(query_idx, query):
    query_fixed = False
    query_progress = [query]
    error_messages = []
    iteration = 0
    while not query_fixed and iteration < 10:
        iteration += 1
        query = query_progress[-1]
        error_message = None
        print('\n')
        print("데이터베이스 엔진 생성 중...")
        engine = create_engine(connection_string)
        df_result = pd.DataFrame()
        print("엔진 생성 성공.")

        if "LIMIT 1" not in query:
            query = query.rstrip(";") + " LIMIT 1;"
        try:
            df_result = pd.read_sql(text(query), con=engine)
            query_fixed = True
            print("✅ sql 쿼리 실행 성공")

        except Exception as e:
            error_message = str(e)
            print("❌ sql 쿼리 실행 실패")

        if engine:
            engine.dispose()
            print("데이터베이스 엔진 연결이 종료되었습니다.\n")

        if not query_fixed or (not df_result.empty and df_result.isnull().values.any()):
            if not df_result.empty:
                row_dict = df_result.iloc[0].to_dict()
            else:
                row_dict = {}

            error_messages.append(error_message)
            time.sleep(3)
            print(f'\n{query_idx+1} - {iteration}번째 API 교정 시도')
            fixed_query = fix_sql_with_llm(query_progress, error_messages, row_dict)
            query_progress.append(extract_sql_query(fixed_query))

    return query_progress, error_messages, query_fixed


# LLM 호출로 쿼리 수정
def fix_sql_with_llm(query_history: list, error_history: list, row_result: dict):
    history_block = ""
    for idx, (q, err) in enumerate(zip(query_history, error_history), 1):
        history_block += f"[Step {idx}]\nError: {err}\nSQL: {q}\n\n"

    prompt = LLM_PROMPT_TEMPLATE.format(history=history_block.strip(), row_result=row_result)

    client = GroqAPIClient()
    response = client.send(system_prompt=prompt, task_type="sql_correction")

    return response


# 전체 처리 파이프라인
def process_sql_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as infile:
        for query_idx, line in tqdm(enumerate(infile)):
            print('\n')
            item = json.loads(line)
            sql_query = item["sql_query"]
            query_progress, error_messages, query_fixed = test_and_correct_sql_query(query_idx, sql_query)

            final_query = query_progress[-1] if query_progress else sql_query
            if "LIMIT 1" in final_query:
                final_query = final_query.rstrip("LIMIT 1")
            if len(query_progress) > 1:
                print(f'\n{query_idx+1}번째 쿼리 수정 완료\n\n')
                is_fixed = 1
                if not query_fixed:
                    is_fixed = 2
            if sql_query == final_query:
                is_fixed = 0

            with open(output_path, "a", encoding="utf-8") as f:
                json.dump({
                    "is_fixed": is_fixed,
                    "complexity": item["complexity"],
                    "sql_query": final_query,
                }, f)
                f.write("\n")
            print("✅ jsonl 파일 업데이트 완료")


# 실행 예시
if __name__ == "__main__":
    n = 6
    file_dir = "results"
    process_sql_file(f"{file_dir}/synthetic_sqls_{n}th.jsonl", f"{file_dir}/synthetic_sqls_{n}th_fixed_8.jsonl")
