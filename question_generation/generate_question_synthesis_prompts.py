import json
import os
import sys
import random
import numpy as np
import re
from pathlib import Path
from tqdm import tqdm

base_dir = Path(__file__).resolve().parent.parent / "sql_generation"
sys.path.append(str(base_dir))

from prompt_templates.schema_ddl import table_names, create_statements

style2desc = {
"Formal": '''**Formal Style**
   - Uses standard grammar and vocabulary.
   - Example: Find all students older than 18 years and return their home addresses.''',

"Colloquial": '''**Colloquial Style**
   - Employs informal vocabulary and expressions.
   - Example: Hey! Could you help me find all the students who are over 18? I'd love to know their names and where they live.''',

"Imperative": '''**Imperative Style**
   - Uses command or directive sentences.
   - Example: Could you please gather all the students who are older than 18? I really need to know their names and where they live!''',

"Interrogative": '''**Interrogative Style**
   - Uses question forms.
   - Example: Could you tell me which students are older than 18 and what their home addresses are?''',

"Descriptive": '''**Descriptive Style**
   - Uses detailed descriptions with contextual information.
   - Example: I want to know the names and home addresses of all students older than 18.''',

"Concise": '''**Concise Style**
   - Use short sentences.
   - Example: Students older than 18, return their names and addresses.''',

"Vague": '''**Vague Style**
   - Includes ambiguous vocabulary requiring inference.
   - Example: What are the names and addresses of those older students? (External Knowledge: 'older students' refers to age >= 18.)''',

"Metaphorical": '''**Metaphorical Style**
   - Uses metaphors or metaphorical expressions.
   - Example: Find the names and addresses of those who have reached adulthood. (External Knowledge: 'reached adulthood' refers to age >= 18.)''',

"Multi-turn Dialogue": '''**Multi-turn Dialogue Style**
    - This involves a dialogue to clarify the user's query needs.
    - Example: [{"User": "I want to query some student information."}, {"Assistant": "Which students' information would you like to query?"}, {"User": "Students older than 18."}, {"Assistant": "What other information would you like to know about them?"}, {"User": "Names and addresses."}, {"Assistant": "Is there anything else you need?"}, {"User": "No."}, {"Assistant": "OK, I will help you translate your request into an SQL query."}]'''
}

steps_wo_ek = '''1. **Explain the SQL Query:** Provide a detailed explanation of what the query does.
2. **Generate a Question:** Formulate a natural language question based on the SQL query and explanation.'''

steps_w_ek = '''1. **Explain the SQL Query:** Provide a detailed explanation of what the query does.
2. **Generate a Question:** Formulate a natural language question based on the SQL query and explanation.
3. **External Knowledge:** For Vague or Metaphorical styles, include external knowledge to enhance clarity.'''

steps_multi_round = '''1. **Explain the SQL Query:** Provide a detailed explanation of what the query does.
2. **Generate a Dialogue:** Create a conversation between the User and the Assistant based on the SQL query and its explanation.'''

guidelines_wo_ek = '''1. Clearly describe the columns being selected by the SQL query. For example:
   - "SELECT * ... FROM ..." means "Find all ...";
   - "SELECT f.check_date, f.status, f.remarks, c.year, c.year_min, c.year_max, c.year_average, c.data_quality_score FROM ..." means "Return the check dates, statuses, remarks, years, minimum years, maximum years, average years, and quality scores for ...".
2. Ensure the natural language question accurately captures the semantics of the SQL query, including conditions such as predicates, `ORDER BY`, and `LIMIT` clauses.'''

guidelines_w_ek = '''1. Clearly describe the columns being selected by the SQL query. For example:
   - "SELECT * ... FROM ..." means "Find all ...";
   - "SELECT f.check_date, f.status, f.remarks, c.year, c.year_min, c.year_max, c.year_average, c.data_quality_score FROM ..." means "Return the check dates, statuses, remarks, years, minimum years, maximum years, average years, and quality scores for ...".
2. Ensure the natural language question accurately captures the semantics of the SQL query, including conditions such as predicates, `ORDER BY`, and `LIMIT` clauses.
3. If necessary, incorporate external knowledge using multiple entries separated by semicolons (";"). These can include formulas, common sense, domain-specific knowledge, or extended context, such as information from long documents. Each entry should be concise.'''

guidelines_multi_round = '''1. Clearly describe the columns being selected by the SQL query. For example:
   - "SELECT * ... FROM ..." means "Find all ...";
   - "SELECT f.check_date, f.status, f.remarks, c.year, c.year_min, c.year_max, c.year_average, c.data_quality_score FROM ..." means "Return the check dates, statuses, remarks, years, minimum years, maximum years, average years, and quality scores for ...".
2. Ensure the conversation accurately captures the semantics of the SQL query, including conditions such as predicates, `ORDER BY`, and `LIMIT` clauses.'''

output_format_wo_ek = '''Please structure your response as follows:

[EXPLANATION-START]
(SQL Explanation)
[EXPLANATION-END]

[QUESTION-START]
(Natural Language Question)
[QUESTION-END]

- **SQL Explanation**: Provide a clear and detailed explanation of the SQL query, enclosed within [EXPLANATION-START] and [EXPLANATION-END].
- **Natural Language Question**: Translate the SQL query into a natural language question, enclosed within [QUESTION-START] and [QUESTION-END].'''

output_format_w_ek = '''Please structure your response as follows:

[EXPLANATION-START]
(SQL Explanation)
[EXPLANATION-END]

[QUESTION-START]
(Natural Language Question)
[QUESTION-END]

[EXTERNAL-KNOWLEDGE-START]
(External Knowledge)
[EXTERNAL-KNOWLEDGE-END]

- **SQL Explanation**: Provide a clear and detailed explanation of the SQL query, enclosed within [EXPLANATION-START] and [EXPLANATION-END].
- **Natural Language Question**: Translate the SQL query into a natural language question, enclosed within [QUESTION-START] and [QUESTION-END].
- **External Knowledge**: Include any relevant external knowledge if applicable, enclosed within [EXTERNAL-KNOWLEDGE-START] and [EXTERNAL-KNOWLEDGE-END]. Leave this section blank if not needed.'''

output_format_multi_round = '''Please structure your response as follows:

[EXPLANATION-START]
(SQL Explanation)
[EXPLANATION-END]

[QUESTION-START]
(Natural Language Question, in the format of [{"User": ...}, {"Assistant": ...}, {"User": ...}, ....])
[QUESTION-END]

- **SQL Explanation**: Provide a clear and detailed explanation of the SQL query, enclosed within [EXPLANATION-START] and [EXPLANATION-END].
- **Natural Language Question**: Convert the SQL query into a multi-round dialogue, enclosed within [QUESTION-START] and [QUESTION-END]. Represent this as a list that captures multiple rounds of conversation between the User and the Assistant.'''

instruction_wo_ek = "Based on the above information, follow the reasoning steps to generate the explanation and the question corresponding to the SQL query."

instruction_w_ek = "Based on the above information, follow the reasoning steps to generate the explanation, the question, and the external knowledge corresponding to the SQL query."

instruction_multi_round = "Based on the above information, follow the reasoning steps to generate the explanation and the dialogue corresponding to the SQL query."


def extract_table_and_column_info(create_statements):
    table_descriptions = []

    # 정규표현식
    table_pattern = re.compile(
        r'CREATE TABLE\s+\w+\.(\w+)\s*\(.*?--\s*table description:\s*(.+?)(?=\n)',
        re.DOTALL
    )
    # -- 가 붙은 주석을 가진 모든 컬럼 줄 → 타입, NULL 여부 무시
    column_pattern = re.compile(
        r'"(\w+)"[^\n]*?--\s*(.+?)(?=\n)'
    )

    for create_stmt in create_statements:
        column_info = []

        # 1. 테이블 설명 추출
        table_match = table_pattern.search(create_stmt)
        if table_match:
            table_name = table_match.group(1).strip()
            table_desc = table_match.group(2).strip()
            column_info.append({
                "table_name": table_name,
                "table_description": table_desc
            })

        # 2. 칼럼 설명 추출
        column_matches = column_pattern.findall(create_stmt)
        for col_name, col_desc in column_matches:
            column_info.append({
                "name": col_name.strip(),
                "description": col_desc.strip()
            })

        table_descriptions.append(column_info)

    return table_descriptions


def group_column_info_by_table(column_info):
    tables = dict()
    current_table = None

    for item in column_info:
        if 'table_name' in item:
            current_table = item['table_name']
            tables[current_table] = {
                'description': item['table_description'],
                'columns': []
            }
        elif current_table and 'name' in item:
            tables[current_table]['columns'].append(item)

    return tables


def extract_used_column_map(sql_query, table_map):
    sql_lower = sql_query.lower()
    used_map = dict()

    for table, info in table_map.items():
        if table.lower() in sql_lower:
            used_map[f"[{table}]"] = info['description']
            for col in info['columns']:
                if col['name'].lower() in sql_lower:
                    used_map[col['name']] = col['description']

    return used_map


if __name__ == "__main__":
    random.seed(42)
    sql_infos = []
    with open(os.path.join(base_dir, "results/synthetic_sqls.jsonl"), "r", encoding="utf-8") as f:
        for line in f:
            sql_infos.append(json.loads(line))
    question_synthesis_template = open("./prompt_templates/question_synthesis_prompt.txt").read()
    styles = ["Formal", "Colloquial", "Imperative", "Interrogative", "Descriptive", "Concise", "Vague", "Metaphorical", "Multi-turn Dialogue"]

    table_names, create_statements = table_names, create_statements
    column_info = extract_table_and_column_info(create_statements)

    prompts = []
    table_map = group_column_info_by_table(column_info)
    for sql_info in tqdm(sql_infos):
        style_name = random.sample(styles, 1)[0]
        column_name2column_desc = column_info
        used_column_name2column_desc = extract_used_column_map(sql_info["sql_query"], table_map)

        if style_name in ["Vague", "Metaphorical"]: # "Vague" and "Metaphorical" styles require external knowledge
            steps = steps_w_ek
            guidelines = guidelines_w_ek
            instruction = instruction_w_ek
            output_format = output_format_w_ek
        elif style_name == "Multi-turn Dialogue": # the "Multi-turn Dialogue" style uses a special multi-round format
            steps = steps_multi_round
            guidelines = guidelines_multi_round
            instruction = instruction_multi_round
            output_format = output_format_multi_round
        else:
            steps = steps_wo_ek
            guidelines = guidelines_wo_ek
            instruction = instruction_wo_ek
            output_format = output_format_wo_ek

        prompt = question_synthesis_template.format(
            style_desc = style2desc[style_name].strip(),
            engine = "SQLite",
            column_info = json.dumps(used_column_name2column_desc, indent = 2, ensure_ascii = False).strip(),
            complexity = sql_info["complexity"],
            sql = sql_info["sql_query"].strip(),
            steps = steps.strip(),
            guidelines = guidelines.strip(),
            output_format = output_format.strip(),
            instruction = instruction.strip()
        )
        
        sql_info["style"] = style_name
        sql_info["prompt"] = prompt

    Path("prompts").mkdir(parents=True, exist_ok=True)
    with open(f"prompts/question_generation_prompts.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(sql_infos, indent=2, ensure_ascii=False))
    print(f"✅ prompts/question_generation_prompts.json 에 저장 완료")