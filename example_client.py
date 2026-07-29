#!/usr/bin/env python3
"""
Пример использования MoonProxy клиента

Этот скрипт показывает, как использовать MoonProxy для отправки запросов
к различным LLM API через единый интерфейс.
"""

import requests
import os
from typing import List, Dict, Optional

class MoonProxyClient:
    """Клиент для работы с MoonProxy"""

    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None):
        """
        Инициализация клиента

        Args:
            base_url: URL MoonProxy сервера
            token: JWT токен для аутентификации (может быть прочитан из файла)
        """
        self.base_url = base_url.rstrip('/')
        self.token = token or self._load_token_from_file()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _load_token_from_file(self, filename: str = "last_token.txt") -> Optional[str]:
        """Загрузка токена из файла"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"⚠️  Не удалось загрузить токен из файла: {e}")
        return None

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """
        Отправка запроса к chat completions endpoint

        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "..."}]
            model: Название модели (опционально, если указано в токене)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов

        Returns:
            Ответ от API в формате словаря
        """
        url = f"{self.base_url}/v1/chat/completions"

        payload = {
            "messages": messages,
            "temperature": temperature
        }

        if model:
            payload["model"] = model
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при отправке запроса: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            raise

    def simple_chat(self, prompt: str, **kwargs) -> str:
        """
        Простой интерфейс для одиночного сообщения

        Args:
            prompt: Текст сообщения
            **kwargs: Дополнительные параметры для chat_completion

        Returns:
            Текст ответа от модели
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(messages, **kwargs)

        # Извлечение текста ответа (формат может отличаться для разных провайдеров)
        try:
            # OpenAI формат
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            # Anthropic формат
            elif "content" in response and len(response["content"]) > 0:
                return response["content"][0]["text"]
            else:
                return str(response)
        except (KeyError, IndexError) as e:
            print(f"⚠️  Не удалось извлечь текст ответа: {e}")
            return str(response)


def main():
    """Примеры использования клиента"""

    # Чтение токена из переменной окружения или файла
    token = os.getenv("MOONPROXY_TOKEN")
    base_url = os.getenv("MOONPROXY_URL", "http://localhost:8000")

    # Инициализация клиента
    client = MoonProxyClient(base_url=base_url, token=token)

    print("🚀 MoonProxy клиент инициализирован\n")

    # Пример 1: Простое сообщение
    print("📝 Пример 1: Простое сообщение")
    print("-" * 50)

    try:
        response = client.simple_chat(
            "Привет! Расскажи мне о Docker в простых терминах.",
            temperature=0.7
        )
        print(f"Ответ: {response}\n")
    except Exception as e:
        print(f"Ошибка: {e}\n")

    # Пример 2: Диалог с контекстом
    print("📝 Пример 2: Диалог с контекстом")
    print("-" * 50)

    try:
        messages = [
            {"role": "system", "content": "Ты - полезный ассистент, который объясняет технические концепции простым языком."},
            {"role": "user", "content": "Что такое Kubernetes?"},
            {"role": "assistant", "content": "Kubernetes - это система для управления контейнеризованными приложениями..."},
            {"role": "user", "content": "А чем он отличается от Docker?"}
        ]

        response = client.chat_completion(
            messages=messages,
            temperature=0.5
        )

        if "choices" in response and len(response["choices"]) > 0:
            print(f"Ответ: {response['choices'][0]['message']['content']}\n")
        else:
            print(f"Ответ: {response}\n")

    except Exception as e:
        print(f"Ошибка: {e}\n")

    # Пример 3: С указанием модели
    print("📝 Пример 3: С указанием модели")
    print("-" * 50)

    try:
        response = client.simple_chat(
            "Напиши короткое стихотворение о программировании",
            model="gpt-4",
            temperature=0.9,
            max_tokens=150
        )
        print(f"Ответ: {response}\n")

    except Exception as e:
        print(f"Ошибка: {e}\n")


if __name__ == "__main__":
    # Проверка наличия токена
    if not os.path.exists("last_token.txt") and not os.getenv("MOONPROXY_TOKEN"):
        print("❌ Токен не найден. Создайте токен с помощью create_token.py")
        print("Пример: python create_token.py --provider openai --api-key sk-...")
    else:
        main()
