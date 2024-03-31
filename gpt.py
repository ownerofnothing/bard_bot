import requests
from transformers import AutoTokenizer
from config import *


class GPT:
    def __init__(self, system_content="Ты - дружелюбный помощник для решения задач по математике. "
                                      "Давай подробный ответ с решением на русском языке"):
        self.system_content = system_content
        self.URL = "gpt://<идентификатор_каталога>/yandexgpt-lite/latest"
        self.HEADERS = {"Content-Types": "application/json"}
        self.MAX_TOKENS = 30
        self.assistant_content = " "


    @staticmethod
    def count_tokens(prompt):
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.1")  # название модели
        return len(tokenizer.encode(prompt))

    def process_resp(self, response) -> [bool, str]:
        if response.status_code < 200 or response.status_code >= 300:
            return False, f"Ошибка: {response.status_code}"
        try:
            full_response = response.json()
        except:
            return False, "Ошибка получения JSON"
        if "error" in full_response or 'choices' not in full_response:
            return False, f"Ошибка: {full_response}"

        result = full_response['choices'][0]['message']['content']

        if result == "":
            return True, "Конец объяснения"

        return True, result

    def make_promt(self, user_history):
        json = {
            "messages": [
                {"role": "system", "content": user_history['system_content']},
                {"role": "user", "content": user_history['user_content']},
                {"role": "assistant", "content": user_history['assistant_content']}
            ],
            "temperature": 1.2,
            "max_tokens": self.MAX_TOKENS,
        }
        return json

    def send_request(self, json):
        resp = requests.post(url=self.URL, headers=self.HEADERS, json=json)
        return resp

    def save_history(self, assistant_content, content_response):
        return f"{assistant_content} {content_response}"
