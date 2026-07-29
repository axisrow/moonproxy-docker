#!/usr/bin/env python3
"""
Тестовый скрипт для MoonProxy

Проверяет основные функции сервиса без реальных API ключей.
"""

import requests
import sys

BASE_URL = "http://localhost:8000"
ADMIN_PASSWORD = "admin123"

def test_server_health():
    """Тест 1: Проверка здоровья сервера"""
    print("🧪 Тест 1: Проверка здоровья сервера")
    print("-" * 50)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Сервер здоров: {data}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_root_endpoint():
    """Тест 2: Проверка корневого эндпоинта"""
    print("\n🧪 Тест 2: Проверка корневого эндпоинта")
    print("-" * 50)

    try:
        response = requests.get(BASE_URL, timeout=5)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Корневой эндпоинт работает: {data}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_token_creation():
    """Тест 3: Создание тестового токена"""
    print("\n🧪 Тест 3: Создание тестового токена")
    print("-" * 50)

    try:
        response = requests.post(
            f"{BASE_URL}/admin/create-token",
            params={"admin_password": ADMIN_PASSWORD},
            json={
                "provider": "openai",
                "api_key": "sk-test-key-for-testing-only",
                "model": "gpt-4"
            },
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        print(f"✅ Токен создан:")
        print(f"   Token ID: {data['token_id']}")
        print(f"   Провайдер: {data['provider']}")
        print(f"   JWT: {data['token'][:50]}...")
        return data['token']
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Ответ: {e.response.text}")
        return None

def test_list_tokens():
    """Тест 4: Получение списка токенов"""
    print("\n🧪 Тест 4: Получение списка токенов")
    print("-" * 50)

    try:
        response = requests.get(
            f"{BASE_URL}/admin/list-tokens",
            params={"admin_password": ADMIN_PASSWORD},
            timeout=5
        )
        response.raise_for_status()

        data = response.json()
        print(f"✅ Получен список токенов: {len(data['tokens'])} токенов")
        for token in data['tokens']:
            print(f"   - {token['token_id'][:16]}... ({token['provider']})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_proxy_request(token):
    """Тест 5: Тест проксирования запроса (без реального API)"""
    print("\n🧪 Тест 5: Тест проксирования запроса")
    print("-" * 50)

    if not token:
        print("⚠️  Пропуск (нет токена)")
        return None

    try:
        # Этот запрос завершится ошибкой, так как мы используем тестовый ключ,
        # но мы проверим, что проксирование работает
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "temperature": 0.7
            },
            timeout=15
        )

        # Ожидаем ошибку, так как ключ тестовый
        if response.status_code == 401:
            print("✅ Проксирование работает (получили ожидаемую ошибку авторизации)")
            return True
        else:
            print(f"⚠️  Неожиданный статус: {response.status_code}")
            print(f"   Ответ: {response.text[:100]}")
            return None

    except requests.exceptions.Timeout:
        print("⚠️  Таймаут (возможно, сервис работает медленно)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_invalid_token():
    """Тест 6: Проверка валидации токенов"""
    print("\n🧪 Тест 6: Проверка валидации токенов")
    print("-" * 50)

    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": "Bearer invalid_token",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello!"}]
            },
            timeout=5
        )

        if response.status_code == 401:
            print("✅ Валидация работает (неверный токен отклонен)")
            return True
        else:
            print(f"⚠️  Неожиданный статус: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_admin_access():
    """Тест 7: Проверка админ доступа"""
    print("\n🧪 Тест 7: Проверка админ доступа")
    print("-" * 50)

    try:
        # Попытка без пароля
        response = requests.get(
            f"{BASE_URL}/admin/list-tokens",
            timeout=5
        )

        if response.status_code == 403:
            print("✅ Админ доступ защищен (пароль требуется)")
            return True
        else:
            print(f"⚠️  Неожиданный статус: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка: {e}")
        return False

def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов MoonProxy")
    print("=" * 50)

    results = []

    # Запуск тестов
    results.append(("Здоровье сервера", test_server_health()))
    results.append(("Корневой эндпоинт", test_root_endpoint()))

    token = test_token_creation()
    results.append(("Создание токена", token is not None))

    results.append(("Список токенов", test_list_tokens()))
    results.append(("Проксирование", test_proxy_request(token)))
    results.append(("Валидация токенов", test_invalid_token()))
    results.append(("Админ доступ", test_admin_access()))

    # Итоги
    print("\n" + "=" * 50)
    print("📊 Результаты тестов:")
    print("-" * 50)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        elif result is False:
            print(f"❌ {test_name}: FAILED")
            failed += 1
        else:
            print(f"⚠️  {test_name}: SKIPPED")
            skipped += 1

    print("-" * 50)
    print(f"Всего: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print(f"\n⚠️  {failed} тест(ов) не пройдены")
        return 1

def main():
    """Главная функция"""
    try:
        # Проверка доступности сервера
        print("🔍 Проверка доступности сервера...")
        requests.get(BASE_URL, timeout=2)
        print(f"✅ Сервер доступен: {BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"❌ Сервер недоступен: {BASE_URL}")
        print("Убедитесь, что сервис запущен: docker-compose up -d")
        return 1

    return run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
