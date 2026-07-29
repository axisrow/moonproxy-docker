# MoonProxy Docker 🚀

Сервис для проксирования запросов к LLM API с управлением токенами и единым IP-адресом.

## 🎯 Особенности

- **🔒 Безопасность**: Храните реальные API ключи только на сервере
- **🎛️ Управление токенами**: Создавайте и отслеживайте отдельные токены для разных проектов
- **🌍 Единый IP**: Все запросы идут через один адрес
- **📊 Мониторинг**: Отслеживайте использование токенов
- **🔄 Множество провайдеров**: OpenAI, Anthropic, OpenRouter и другие
- **🐳 Простой Docker**: Быстрое развертывание одной командой

## ⚡ Быстрый старт

### Вариант 1: Автоматический запуск (рекомендуется)

```bash
chmod +x start.sh
./start.sh
```

Скрипт автоматически:
- Проверит зависимости
- Создаст необходимую структуру директорий
- Сгенерирует безопасные пароли
- Соберёт и запустит Docker контейнеры
- Проверит работоспособность

### Вариант 2: Ручной запуск

```bash
# Создание директорий
make init

# Запуск сервиса
make up

# Проверка здоровья
make health
```

## 📖 Использование

### 1️⃣ Создание токена

**Автоматический способ:**

```bash
python create_token.py --provider openai --api-key sk-your-key --model gpt-4
```

**Ручной способ:**

```bash
curl -X POST http://localhost:8000/admin/create-token \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-your-key",
    "model": "gpt-4"
  }' \
  --data-urlencode "admin_password=YOUR_ADMIN_PASSWORD"
```

**Пример ответа:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_id": "abc123...",
  "provider": "openai",
  "model": "gpt-4",
  "created_at": "2024-01-15T10:30:00"
}
```

### 2️⃣ Использование токена

**Python:**

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {YOUR_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
)

print(response.json())
```

**JavaScript/Node.js:**

```javascript
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${YOUR_TOKEN}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4',
    messages: [
      { role: 'user', content: 'Hello!' }
    ]
  })
});

const data = await response.json();
console.log(data);
```

### 3️⃣ Управление токенами

**Просмотр списка:**

```bash
curl "http://localhost:8000/admin/list-tokens?admin_password=YOUR_PASSWORD"
```

**Удаление токена:**

```bash
curl -X DELETE "http://localhost:8000/admin/delete-token/TOKEN_ID?admin_password=YOUR_PASSWORD"
```

## 🔧 Поддерживаемые провайдеры

| Провайдер | Параметр `provider` | Пример endpoint |
|-----------|---------------------|-----------------|
| OpenAI | `openai` | `https://api.openai.com/v1/chat/completions` |
| Anthropic | `anthropic` | `https://api.anthropic.com/v1/messages` |
| OpenRouter | `openrouter` | `https://openrouter.ai/api/v1/chat/completions` |
| Кастомный | Любое значение | Укажите `endpoint` при создании токена |

## 🛠️ Команды управления

```bash
make help          # Показать все команды
make up            # Запустить сервисы
make down          # Остановить сервисы
make restart       # Перезапустить сервисы
make logs          # Посмотреть логи
make health        # Проверить здоровье сервиса
make clean         # Полная очистка
make build         # Пересобрать образы
```

## 📁 Структура проекта

```
moonproxy_docker/
├── main.py              # Основное приложение FastAPI
├── Dockerfile           # Docker конфигурация
├── docker-compose.yml   # Docker Compose конфигурация
├── requirements.txt     # Python зависимости
├── create_token.py      # Скрипт для создания токенов
├── example_client.py    # Пример использования клиента
├── test_moonproxy.py    # Тестовый скрипт
├── start.sh            # Скрипт быстрого старта
├── Makefile            # Команды управления
├── .env.example        # Пример переменных окружения
├── README.md           # Эта документация
├── FAQ.md              # Часто задаваемые вопросы
├── data/               # Директория для данных (создаётся автоматически)
└── config/             # Директория для конфигов (создаётся автоматически)
```

## 🔐 Безопасность в продакшене

### ✅ Обязательно сделайте:

1. **Измените дефолтные пароли** в `.env`:
   ```bash
   MOONPROXY_SECRET_KEY=your-very-long-and-secure-secret-key
   MOONPROXY_ADMIN_PASSWORD=your-secure-admin-password
   ```

2. **Ограничьте доступ** к API:
   - Используйте firewall
   - Настройте reverse proxy с авторизацией
   - Ограничьте доступ по IP

3. **Используйте HTTPS** в продакшене:
   - Настройте SSL/TLS сертификаты
   - Используйте reverse proxy (Nginx, Caddy)

4. **Регулярно бэкапьте** данные из директории `data/`

### ⚠️ Никогда не:

- Не храните `.env` файл в git репозитории
- Не используйте дефолтные пароли в продакшене
- Не открывайте API всему интернету без защиты
- Не передавайте токены через незащищённые каналы

## 🧪 Тестирование

```bash
# Запуск всех тестов
python test_moonproxy.py

# Пример использования клиента
python example_client.py
```

## 📚 Дополнительная документация

- **[FAQ.md](FAQ.md)** - Часто задаваемые вопросы
- **[.env.example](.env.example)** - Пример конфигурации
- **[example_client.py](example_client.py)** - Примеры кода

## 🐛 Troubleshooting

### Сервис не запускается

```bash
# Проверьте логи
make logs

# Перезапустите сервис
make restart

# Полная пересборка
make down
make build
make up
```

### Проблемы с доступом

```bash
# Проверьте, работает ли сервис
curl http://localhost:8000/health

# Проверьте порты
docker ps
```

### Ошибка "Invalid token"

1. Проверьте срок действия токена (1 год)
2. Убедитесь, что `MOONPROXY_SECRET_KEY` не изменялся
3. Создайте новый токен

## 🔄 Обновление

```bash
# Остановка сервиса
make down

# Обновление кода
git pull

# Пересборка и запуск
make build
make up
```

## 📊 Мониторинг

### Health check

```bash
curl http://localhost:8000/health
```

**Пример ответа:**

```json
{
  "status": "healthy",
  "tokens_count": 5,
  "timestamp": "2024-01-15T12:00:00"
}
```

### Просмотр логов

```bash
# Все логи
make logs

# Только ошибки
docker-compose logs moonproxy | grep ERROR
```

## 🤝 Интеграция с проектами

### Быстрая замена в существующем проекте

**Было:**
```python
response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer sk-your-openai-key"},
    json={...}
)
```

**Стало:**
```python
response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={"Authorization": f"Bearer {MOONPROXY_TOKEN}"},
    json={...}
)
```

### Множественные проекты

```bash
# Проект 1 (OpenAI)
python create_token.py --provider openai --api-key sk-... --model gpt-4

# Проект 2 (Anthropic)
python create_token.py --provider anthropic --api-key sk-ant-...

# Проект 3 (OpenRouter)
python create_token.py --provider openrouter --api-key sk-or-...
```

## 📝 Лицензия

MIT License

## 🙏 Поддержка

Если у вас есть вопросы или проблемы:

1. Проверьте [FAQ.md](FAQ.md)
2. Посмотрите логи: `make logs`
3. Запустите тесты: `python test_moonproxy.py`
4. Изучите примеры в `example_client.py`

---

**Создано с ❤️ для удобного управления LLM API**