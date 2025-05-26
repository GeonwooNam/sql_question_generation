import json
import re
import os
import time
from tqdm import tqdm
from llm_api import GroqAPIClient


def parse_response(response):
    pattern = r"```sql\s*(.*?)\s*```"
    
    sql_blocks = re.findall(pattern, response, re.DOTALL)

    if sql_blocks:
        raw_sql = sql_blocks[-1].strip()
    else:
        # Try fallback: look for standalone SQL starting with SELECT / WITH
        fallback_match = re.search(r"(SELECT|WITH|INSERT|UPDATE|DELETE)\s.+", response, re.IGNORECASE | re.DOTALL)
        if fallback_match:
            raw_sql = fallback_match.group(0).strip()
        else:
            print("❌ No SQL found.")
            return ""

        # Normalize newlines to space
    flat_sql = raw_sql.replace("\\n", " ").replace("\n", " ")
    flat_sql = re.sub(r"\s+", " ", flat_sql).strip()

    return flat_sql


def save_result_to_jsonl(prompt, db_id, response, complexity, filepath="results/llm_results.jsonl"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "a", encoding="utf-8") as f:
        json.dump({
            "complexity": complexity,
            "sql_query": parse_response(response),
            # "prompt": prompt,
            # "db_id": db_id,
        }, f)
        f.write("\n")
    print("✅ jsonl 파일 업데이트 완료")


def llm_inference(prompts, db_ids, complexities, output_file):
    """
    Generates responses using an LLM for given prompts.

    Args:
        prompts (list of str): A list of prompts for the model.
        db_ids (list of str): A list of database IDs corresponding to each prompt.
        output_file (str): File path to write the llm outputs.

    Returns:
        list of dict: A list of dictionaries containing the prompt, db_id, and generated response.
    """

    llm_results = []

    for i, (db_id, prompt, complexity) in tqdm(enumerate(zip(db_ids, prompts, complexities))):

        client = GroqAPIClient()
        response = client.send(system_prompt=prompt, task_type="sql_generation")

        if response is not None:
            print("✅ LLM 답변 완료")
        else:
            print("❌❌ LLM 답변 실패")

        llm_results.append(response)
        save_result_to_jsonl(prompt, db_id, response, complexity, filepath=output_file)
        client.close()

        if i < len(prompts) - 1:
            time.sleep(30)

    return llm_results


if __name__ == '__main__':
    with open("prompts/sql_synthesis_prompts.json", encoding="utf-8") as f:
        input_dataset = json.load(f)
    output_file = "results/llm_results.jsonl"

    db_ids = [data["db_id"] for data in input_dataset]
    prompts = [data["prompt"] for data in input_dataset]
    complexities = [data["complexity"] for data in input_dataset]
    
    results = llm_inference(prompts, db_ids, complexities, output_file)
