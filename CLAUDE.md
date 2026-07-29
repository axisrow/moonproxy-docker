# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект MoonProxy Docker

MoonProxy - это FastAPI сервис для проксирования запросов к LLM API с управлением токенами и единым IP-адресом. Сервис позволяет создавать токены для разных провайдеров (OpenAI, Anthropic, OpenRouter) и отслеживать их использование.

## Ключевые команды для разработки

### Docker команды (основной способ запуска)
```bash
# Инициализация проекта - создание директорий
make init

# Запуск сервисов
make up

# Остановка сервисов
make down

# Перезапуск сервисов
make restart

# Просмотр логов
make logs

# Проверка здоровья сервиса
make health

# Полная очистка
make clean

# Пересборка образов
make build

# Shell в контейнере
make shell
```

### Локальная разработка
```bash
# Установка зависимостей
make install

# Запуск в режиме разработки с автоперезагрузкой
make dev

# Запуск тестов
make test
python test_moonproxy.py
```

### Создание и управление токенами
```bash
# Создание токена через скрипт
python create_token.py --provider openai --api-key sk-... --model gpt-4

# Создание токена через API
curl -X POST http://localhost:8000/admin/create-token \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "api_key": "sk-...", "model": "gpt-4"}' \
  --data-urlencode "admin_password=admin123"
```

## Архитектура приложения

### Основной файл: main.py
**FastAPI приложение** с тремя основными группами эндпоинтов:

1. **Admin эндпоинты** (`/admin/*`):
   - `POST /admin/create-token` - создание новых токенов (требует админ пароль)
   - `GET /admin/list-tokens` - список всех токенов
   - `DELETE /admin/delete-token/{token_id}` - удаление токена

2. **Proxy эндпоинт** (`/v1/chat/completions`):
   - Проксирует запросы к реальным API провайдерам
   - Верифицирует JWT токены
   - Поддерживает OpenAI, Anthropic, OpenRouter форматы
   - Реализует ограничение по времени для моделей

3. **Service эндпоинты**:
   - `GET /` - информация о сервисе
   - `GET /health` - проверка здоровья

### Управление токенами
- Токены хранятся в `/app/data/tokens.json` (примонтирован как volume)
- JWT токены создаются с сроком действия 1 год
- Каждый токен содержит: `provider`, `api_key`, `model`, `endpoint`
- При создании токена проверяется на дубликаты по `api_key` + `provider`

### Временные ограничения для моделей
**Важно:** Сервис реализует ограничение по времени (UTC+8):
- В окно 14:00-18:00 (UTC+8) доступны только бесплатные модели GLM Flash
- Список бесплатных моделей: `glm-4.7-flash`, `glm-4.5-flash`, `glm-4.6v-flash`
- Функция `enforce_model_window()` проверяет модель и время запроса

### Поддерживаемые провайдеры
- **OpenAI**: стандартный формат `/v1/chat/completions`
- **Anthropic**: формат `/v1/messages` с заголовками `x-api-key`
- **OpenRouter**: формат `/v1/chat/completions`
- **Кастомные**: любой endpoint через параметр `endpoint`

## Конфигурация

### Переменные окружения
Основные переменные в `.env` (используйте `.env.example` как шаблон):
- `MOONPROXY_SECRET_KEY` - секретный ключ для JWT (обязательно изменить в продакшене)
- `MOONPROXY_ADMIN_PASSWORD` - админ пароль (обязательно изменить в продакшене)
- `MOONPROXY_DATABASE_URL` - URL базы данных (SQLite по умолчанию)
- `MOONPROXY_LOG_LEVEL` - уровень логирования
- `MOONPROXY_PORT` - порт сервиса (8000 по умолчанию)
- `MOONPROXY_HOST` - хост для привязки (0.0.0.0 по умолчанию)

### Volume mounts
- `./data:/app/data` - хранение токенов и данных
- `./config:/app/config` - конфигурационные файлы

## Тестирование

### Основной тестовый скрипт: test_moonproxy.py
Запускает 7 тестов:
1. Проверка здоровья сервера
2. Проверка корневого эндпоинта
3. Создание тестового токена
4. Получение списка токенов
5. Тест проксирования запроса
6. Проверка валидации токенов
7. Проверка админ доступа

```bash
# Запуск всех тестов
python test_moonproxy.py
```

### Примеры клиентов
- `example_client.py` - примеры использования на Python
- `create_token.py` - CLI скрипт для создания токенов

## Безопасность в продакшене

**Критически важные шаги для продакшена:**
1. Измените `MOONPROXY_SECRET_KEY` на сложное значение
2. Измените `MOONPROXY_ADMIN_PASSWORD` на надежный пароль
3. Настройте HTTPS через reverse proxy
4. Ограничьте доступ по IP или firewall
5. Не храните `.env` в git репозитории
6. Регулярно бэкапьте директорию `data/`

## Структура проекта

```
moonproxy_docker/
├── main.py              # Основное FastAPI приложение
├── Dockerfile           # Docker конфигурация
├── docker-compose.yml   # Docker Compose конфигурация
├── requirements.txt     # Python зависимости
├── create_token.py      # CLI скрипт для создания токенов
├── test_moonproxy.py    # Основной тестовый скрипт
├── example_client.py    # Примеры использования
├── Makefile            # Команды управления
├── .env.example        # Шаблон переменных окружения
├── start.sh            # Автоматический скрипт старта
├── data/               # Директория для данных (создаётся автоматически)
└── config/             # Директория для конфигов (создаётся автоматически)
```

## Работа с проектом

### Добавление новых провайдеров
Для добавления нового провайдера:
1. Добавьте endpoint в словарь `endpoints` в `main.py`
2. Добавьте логику headers в блоке подготовки headers
3. При необходимости добавьте специфику форматирования запроса

### Отладка проблем
```bash
# Проверка логов
make logs

# Проверка здоровья сервиса
curl http://localhost:8000/health

# Тест в контейнере
docker-compose exec moonproxy python test_moonproxy.py
```

### Обновление зависимостей
1. Обновите `requirements.txt`
2. Пересоберите образ: `make build && make up`