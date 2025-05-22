import json
import random
import os
import pickle
import numpy as np
from pathlib import Path
from tqdm import tqdm

from prompt_templates.schema_ddl import prefixed_table_names, create_statements
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

simple_criterion = '''**Criteria:**
Simple SQL queries may satisfy one or more of the following criteria:
- Simple queries should select data from a single table only.
- Basic aggregate functions are permitted, such as `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`.
- No joins are allowed; the query must operate on a single table.

**Example of Simple SQL Query:**
```sql
SELECT name, department_name
FROM employees
WHERE level > 5
ORDER BY age DESC;
```'''

moderate_criterion = '''**Criteria:**
Moderate SQL queries may satisfy one or more of the following criteria:
- Involves table joins, such as `JOIN`, `INNER JOIN`, `LEFT JOIN`, `CROSS JOIN`, etc.
- Includes subqueries within the `SELECT` or `WHERE` clauses.
- Utilizes aggregate functions alongside a `GROUP BY` clause.
- Contains complex `WHERE` conditions, including `IN`, `BETWEEN`, `LIKE`.
- Incorporate a `HAVING` clause to filter aggregated results.
- Uses aggregate functions like `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, etc.

**Example of Moderate SQL Query:**
```sql
SELECT e.name, d.department_name, AVG(s.salary) AS average_salary
FROM employees e
INNER JOIN departments d ON e.department_id = d.department_id
LEFT JOIN salaries s ON e.employee_id = s.employee_id
WHERE e.age > 30 AND e.status = 'active'
GROUP BY e.name, d.department_name
HAVING AVG(s.salary) > 50000;
```'''

complex_criterion = '''**Criteria:**
Complex SQL queries may satisfy one or more of the following criteria:
- Contains complex nested subqueries.
- Utilizes multiple types of joins, including self-joins.
- Includes window functions, such as `ROW_NUMBER`, `RANK`, etc.
- Uses Common Table Expressions (CTEs) for improved readability.
- Combines multiple aggregate functions.
- Involves complex `WHERE` and `HAVING` clauses with multiple conditions.
- Utilizes advanced functions and operators.

**Example of Complex SQL Query:**
```sql
WITH EmployeeCTE AS (
    SELECT employee_id, name, department_id, ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rank
    FROM employees
)
SELECT e.name, d.department_name
FROM EmployeeCTE e
INNER JOIN departments d ON e.department_id = d.department_id
WHERE e.rank <= 3;
```'''

highly_complex_criterion = '''**Criteria:**
Highly complex SQL queries may satisfy one or more of the following criteria:
- Includes multiple Common Table Expressions (CTEs) for readability.
- Combines nested subqueries and various joins.
- Utilizes recursive CTEs for hierarchical or recursive queries.
- Extensively uses advanced window functions.
- May involve `UNION` or `UNION ALL` to combine result sets.
- Implements complex logic with advanced analytical functions.
- Employs a wide range of SQL clauses and conditions.
- Utilizes a broad spectrum of SQL functions and advanced features.

**Example of Highly Complex SQL Query:**
```sql
WITH RECURSIVE EmployeeHierarchy AS (
    SELECT employee_id, name, manager_id, department_id, 1 as level
    FROM employees
    WHERE manager_id IS NULL
    UNION ALL
    SELECT e.employee_id, e.name, e.manager_id, e.department_id, eh.level + 1
    FROM employees e
    JOIN EmployeeHierarchy eh ON e.manager_id = eh.employee_id
),
DepartmentSalaries AS (
    SELECT eh.employee_id, eh.name, eh.level, d.department_name, s.salary, d.department_id
    FROM EmployeeHierarchy eh
    INNER JOIN departments d ON eh.department_id = d.department_id
    INNER JOIN salaries s ON eh.employee_id = s.employee_id
),
DepartmentStats AS (
    SELECT 
        d.department_id,
        COUNT(e.employee_id) AS employee_count,
        AVG(s.salary) AS average_salary
    FROM employees e
    INNER JOIN salaries s ON e.employee_id = s.employee_id
    INNER JOIN departments d ON e.department_id = d.department_id
    GROUP BY d.department_id
)
SELECT ds.name, ds.level, 
    SUM(ds.salary) OVER (PARTITION BY ds.department_id ORDER BY ds.level, ds.name) AS cumulative_salary
FROM DepartmentSalaries ds
INNER JOIN DepartmentStats dstat ON ds.department_id = dstat.department_id
ORDER BY ds.level, ds.name;
```'''

complexity2criterion = {
    "Simple": simple_criterion,
    "Moderate": moderate_criterion,
    "Complex": complex_criterion,
    "Highly Complex": highly_complex_criterion
}
complexity_weights = [0.15, 0.25, 0.3, 0.3]

# 3. 프롬프트 생성
prompts = []
for i in tqdm(range(32)):  # 원하는 쿼리 수
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
        n_rows = np.random.choice([1, 2])
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
