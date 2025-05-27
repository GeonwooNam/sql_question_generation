import re
import json
from tqdm import tqdm
import os
import sys
import time
from pathlib import Path
from typing import Optional

base_dir = Path(__file__).resolve().parent.parent / "sql_generation"
sys.path.append(str(base_dir))

from llm_api import GroqAPIClient


def extract_question(text: str) -> Optional[str]:
    pattern = r"\[QUESTION-START\](.*?)\[QUESTION-END\]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return None

def save_question_result_to_jsonl(response, complexity, sql_query, style, filepath="results/question_synthesis_llm_output.jsonl"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "a", encoding="utf-8") as f:
        json.dump({
            "complexity": complexity,
            "sql_query": sql_query,
            "style": style,
            "question": extract_question(response)
        }, f)
        f.write("\n")
    print("✅ jsonl 파일 업데이트 완료")



def llm_inference(complexities, sql_queries, styles, prompts, output_file):
    """
    Perform LLM inference to generate multiple responses for each prompt in the dataset.

    Args:
        complexities: A list of complexity.
        sql_queries: A list of sql_query.
        styles: A list of style.
        prompts: A list of prompt.
        output_file: file path to restore output results

    Returns:
    """

    responses_list = []
    for i, (complexity, sql_query, style, prompt) in tqdm(enumerate(zip(complexities, sql_queries, styles, prompts))):

        client = GroqAPIClient()
        response = client.send(system_prompt=prompt, task_type="sql_generation")

        if response is not None:
            print("✅ LLM 답변 완료")
        else:
            print("❌❌ LLM 답변 실패")

        responses_list.append(response)
        save_question_result_to_jsonl(response, complexity, sql_query, style, filepath=output_file)
        client.close()

        if i < len(prompts) - 1:
            time.sleep(15)

    return


if __name__ == '__main__':
    input_dataset = json.load(open("prompts/question_generation_prompts.json"))
    output_file = "results/synthetic_questions.jsonl"

    complexities = [data["complexity"] for data in input_dataset]
    sql_queries = [data["sql_query"] for data in input_dataset]
    styles = [data["style"] for data in input_dataset]
    prompts = [data["prompt"] for data in input_dataset]

    llm_inference(complexities, sql_queries, styles, prompts, output_file)