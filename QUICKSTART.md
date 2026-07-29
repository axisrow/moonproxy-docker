# 🚀 MoonProxy - Краткое руководство

## ⚡ Быстрый старт (3 команды)

```bash
chmod +x start.sh
./start.sh
python create_token.py --provider openai --api-key sk-your-key --model gpt-4
```

## 🎯 Что это?

MoonProxy - это сервис, который позволяет:
- 📱 Использовать один IP-адрес для всех LLM API запросов
- 🔐 Управлять токенами для разных проектов
- 📊 Отслеживать использование API
- 🌍 Поддерживать множество провайдеров (OpenAI, Anthropic, OpenRouter)

## 📝 Основные команды

### Запуск
```bash
./start.sh          # Автоматический запуск
make up              # Ручной запуск
make down            # Остановка
make restart         # Перезапуск
```

### Управление токенами
```bash
python create_token.py --provider openai --api-key sk-... --model gpt-4
python create_token.py --provider anthropic --api-key sk-ant-...
```

### Мониторинг
```bash
make logs            # Логи сервиса
make health          # Проверка здоровья
python test_moonproxy.py  # Запуск тестов
```

## 📖 Пример использования

```python
import requests

# Вместо прямого вызова OpenAI API
# response = requests.post("https://api.openai.com/v1/chat/completions", ...)

# Используйте MoonProxy
response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={"Authorization": f"Bearer {YOUR_MOONPROXY_TOKEN}"},
    json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)
```

## 🔐 Безопасность

**Важно для продакшена:**
1. Измените пароли в `.env` файле
2. Используйте HTTPS
3. Ограничьте доступ по IP
4. Настройте firewall

Подробнее: `DEPLOYMENT.md`

## 📚 Документация

- `README.md` - Полная документация
- `FAQ.md` - Часто задаваемые вопросы
- `DEPLOYMENT.md` - Руководство по развёртыванию
- `example_client.py` - Примеры кода

## 🆘 Проблемы?

```bash
# Проверьте логи
make logs

# Перезапустите сервис
make restart

# Полная переустановка
make down && make build && make up
```

## 📍 URL сервиса

- API: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- Swagger docs (если добавлены): `http://localhost:8000/docs`

---

**Готово к использованию за 2 минуты!** ⏱️