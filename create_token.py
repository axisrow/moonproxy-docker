#!/usr/bin/env python3
"""
Скрипт для создания токенов MoonProxy
Использование: python create_token.py --provider openai --api-key sk-... --model gpt-4
"""

import argparse
import requests
import sys

DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_SERVER_URL = "http://localhost:8000"

def create_token(server_url, admin_password, provider, api_key, model=None, endpoint=None):
    """Создание токена через API"""

    url = f"{server_url}/admin/create-token"
    params = {"admin_password": admin_password}

    payload = {
        "provider": provider,
        "api_key": api_key
    }

    if model:
        payload["model"] = model
    if endpoint:
        payload["endpoint"] = endpoint

    try:
        response = requests.post(url, params=params, json=payload)
        response.raise_for_status()

        data = response.json()
        print("✅ Токен успешно создан!")
        print(f"Токен ID: {data['token_id']}")
        print(f"Провайдер: {data['provider']}")
        print(f"Модель: {data.get('model', 'Не указана')}")
        print(f"JWT Токен: {data['token']}")
        print(f"Создан: {data['created_at']}")

        # Сохранение токена в файл
        with open('last_token.txt', 'w') as f:
            f.write(data['token'])
        print(f"\n💾 Токен сохранён в файл 'last_token.txt'")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при создании токена: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Ответ сервера: {e.response.text}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Создание токенов для MoonProxy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры использования:
  python create_token.py --provider openai --api-key sk-... --model gpt-4
  python create_token.py --provider anthropic --api-key sk-ant-...
  python create_token.py --provider openrouter --api-key sk-or-... --endpoint https://openrouter.ai/api/v1/chat/completions
        '''
    )

    parser.add_argument('--provider', required=True,
                       help='Провайдер API (openai, anthropic, openrouter, etc.)')
    parser.add_argument('--api-key', required=True,
                       help='API ключ провайдера')
    parser.add_argument('--model', help='Модель (опционально)')
    parser.add_argument('--endpoint', help='Кастомный endpoint (опционально)')
    parser.add_argument('--server-url', default=DEFAULT_SERVER_URL,
                       help=f'URL сервера MoonProxy (по умолчанию: {DEFAULT_SERVER_URL})')
    parser.add_argument('--admin-password', default=DEFAULT_ADMIN_PASSWORD,
                       help='Админ пароль (по умолчанию: admin123)')

    args = parser.parse_args()

    # Проверка, что сервер доступен
    try:
        response = requests.get(f"{args.server_url}/health", timeout=5)
        response.raise_for_status()
        print(f"✅ Сервер MoonProxy доступен по адресу {args.server_url}")
    except requests.exceptions.RequestException:
        print(f"❌ Сервер MoonProxy недоступен по адресу {args.server_url}")
        print("Убедитесь, что сервис запущен: docker-compose up -d")
        sys.exit(1)

    # Создание токена
    create_token(
        server_url=args.server_url,
        admin_password=args.admin_password,
        provider=args.provider,
        api_key=args.api_key,
        model=args.model,
        endpoint=args.endpoint
    )

if __name__ == "__main__":
    main()
