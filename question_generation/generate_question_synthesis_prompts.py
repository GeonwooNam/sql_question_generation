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
from prompt_templates.question_templates import (
    style2desc,
    step_map,
    guideline_map,
    output_format_map,
    instruction_map,
)


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
            style_key = "w_ek"
        elif style_name == "Multi-turn Dialogue": # the "Multi-turn Dialogue" style uses a special multi-round format
            style_key = "multi_round"
        else:
            style_key = "wo_ek"

        steps = step_map[style_key]
        guidelines = guideline_map[style_key]
        instruction = instruction_map[style_key]
        output_format = output_format_map[style_key]

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