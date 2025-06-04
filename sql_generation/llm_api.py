import requests
from dotenv import load_dotenv
import os
import time

load_dotenv()
API_KEY = os.getenv("API_KEY")


class GroqAPIClient:
    def __init__(self):
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.session = requests.Session()
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

    def send(self, system_prompt: str, user_prompt: str = "", task_type: str = "sql_generation"):
        if task_type == "sql_generation":
            model = "meta-llama/llama-4-scout-17b-16e-instruct"
            temperature = 0.7
        elif task_type == "question_generation":
            model = "meta-llama/llama-4-scout-17b-16e-instruct"
            # model = "meta-llama/llama-4-maverick-17b-128e-instruct"
            temperature = 0.8
        elif task_type == "sql_correction":
            model = "meta-llama/llama-4-scout-17b-16e-instruct"
            # model = "llama-3.3-70b-versatile"
            temperature = 0.0
        else:
            model = None
            temperature = 0.0

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024
        }

        try:
            print("API 호출 시도 중...")
            start_time = time.time()
            response = self.session.post(self.url, headers=self.headers, json=payload)
            response.raise_for_status()
            duration = time.time() - start_time
            print(f"✅ API 호출 성공 ({duration:.2f} s)")
            return response.json()["choices"][0]["message"]["content"]

        except requests.RequestException as e:
            print(f"❌ API 호출 실패: {e}")
            return None

    def close(self):
        self.session.close()


def main(system_prompt: str, user_prompt: str = ""):
    client = GroqAPIClient()

    while True:
        result = client.send(system_prompt, task_type="sql_generation")

        if result is not None:
            print("✅ 응답:", result)
        else:
            print("🔁 세션 재연결 중...")
            client.close()
            time.sleep(2)  # 잠깐 대기 후
            client = LLMClient()  # 새로 세션 생성
            continue  # 다음 루프에서 재시도

        time.sleep(60)  # 1분 간격 호출

