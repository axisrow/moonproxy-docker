# MoonProxy - Часто задаваемые вопросы

## Общие вопросы

### Что такое MoonProxy?

MoonProxy - это сервис для проксирования запросов к различным LLM API (Large Language Model) с возможностью управления собственными токенами и использования единого IP-адреса для всех проектов.

### Зачем нужен MoonProxy?

- **Единая точка доступа**: Управляйте всеми LLM API через один сервис
- **Безопасность**: Храните реальные API ключи только на сервере MoonProxy
- **Удобство**: Используйте короткие JWT токены вместо длинных API ключей
- **Мониторинг**: Отслеживайте использование токенов и время последнего доступа
- **Гибкость**: Поддержка множества провайдеров через единый интерфейс

## Установка и настройка

### Как быстро начать работу?

```bash
# 1. Клонируйте или перейдите в директорию проекта
cd moonproxy_docker

# 2. Создайте необходимые директории
make init

# 3. Настройте переменные окружения (опционально)
cp .env.example .env
# Отредактируйте .env, изменив пароли и ключи

# 4. Запустите сервис
make up

# 5. Проверьте здоровье сервиса
make health
```

### Как изменить админ пароль?

Отредактируйте файл `docker-compose.yml` или `.env`:

```yaml
environment:
  - MOONPROXY_ADMIN_PASSWORD=your-secure-password
```

Затем перезапустите сервис:

```bash
make restart
```

### Как изменить секретный ключ для JWT?

```yaml
environment:
  - MOONPROXY_SECRET_KEY=your-very-long-and-secure-secret-key
```

**Важно**: При изменении секретного ключа все существующие JWT токены станут недействительными.

## Использование

### Как создать токен?

**Способ 1: Через скрипт**

```bash
python create_token.py \
  --provider openai \
  --api-key sk-your-openai-api-key \
  --model gpt-4
```

**Способ 2: Через API напрямую**

```bash
curl -X POST http://localhost:8000/admin/create-token \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-your-openai-api-key",
    "model": "gpt-4"
  }' \
  --data-urlencode "admin_password=admin123"
```

### Как использовать токен?

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
        ],
        "temperature": 0.7
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
    ],
    temperature: 0.7
  })
});

const data = await response.json();
console.log(data);
```

### Какие провайдеры поддерживаются?

- **OpenAI**: `provider: "openai"`
- **Anthropic**: `provider: "anthropic"`
- **OpenRouter**: `provider: "openrouter"`
- **Кастомные endpoint**: Укажите `endpoint` при создании токена

### Как использовать кастомный endpoint?

```bash
python create_token.py \
  --provider custom \
  --api-key your-api-key \
  --endpoint https://your-custom-endpoint.com/v1/chat/completions
```

## Управление токенами

### Как посмотреть список всех токенов?

```bash
curl "http://localhost:8000/admin/list-tokens?admin_password=admin123"
```

**Пример ответа:**

```json
{
  "tokens": [
    {
      "token_id": "abc123...",
      "provider": "openai",
      "model": "gpt-4",
      "created_at": "2024-01-15T10:30:00",
      "last_used": "2024-01-15T11:45:00"
    }
  ]
}
```

### Как удалить токен?

```bash
curl -X DELETE "http://localhost:8000/admin/delete-token/TOKEN_ID?admin_password=admin123"
```

### Как долго действуют токены?

JWT токены действуют 1 год с момента создания. После этого нужно будет создать новый токен.

### Можно ли изменить срок действия токена?

Да, отредактируйте файл `main.py` в функции `generate_jwt_token`:

```python
payload = {
    'token_id': token_id,
    'exp': datetime.now() + timedelta(days=365)  # Измените количество дней
}
```

## Безопасность

### Как защитить MoonProxy в продакшене?

1. **Измените дефолтные пароли**: Замените `MOONPROXY_SECRET_KEY` и `MOONPROXY_ADMIN_PASSWORD`
2. **Используйте HTTPS**: Настройте SSL/TLS сертификаты
3. **Ограничьте доступ**: Используйте firewall или reverse proxy
4. **Регулярно обновляйте**: Следите за обновлениями зависимостей
5. **Бэкап данных**: Регулярно бэкапьте директорию `data/`

### Как настроить HTTPS?

Используйте reverse proxy вроде Nginx или Caddy:

**Caddy (автоматический HTTPS):**

```
moonproxy.yourdomain.com {
    reverse_proxy localhost:8000
}
```

**Nginx:**

```nginx
server {
    listen 443 ssl;
    server_name moonproxy.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Как ограничить доступ по IP?

Отредактируйте `main.py`, добавив middleware для проверки IP:

```python
from fastapi import Request, HTTPException

ALLOWED_IPS = ["192.168.1.100", "10.0.0.1"]

@app.middleware("http")
async def ip_restriction(request: Request, call_next):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail="Access denied")
    response = await call_next(request)
    return response
```

## Мониторинг и логирование

### Как посмотреть логи сервиса?

```bash
make logs
```

или

```bash
docker-compose logs -f moonproxy
```

### Как проверить здоровье сервиса?

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

### Как включить детальное логирование?

Измените переменную окружения:

```yaml
environment:
  - MOONPROXY_LOG_LEVEL=DEBUG
```

## Проблемы и решения

### Сервис не запускается

**Проверьте логи:**

```bash
docker-compose logs moonproxy
```

**Общие решения:**

1. Убедитесь, что порт 8000 не занят: `lsof -i :8000`
2. Проверьте права доступа к директории `data/`
3. Убедитесь, что Docker запущен: `docker ps`

### Ошибка "Invalid token"

1. Проверьте, что токен не истек (срок действия 1 год)
2. Убедитесь, что `MOONPROXY_SECRET_KEY` не изменялся
3. Проверьте формат токена: должен быть JWT

### Ошибка "Invalid admin password"

1. Проверьте пароль в `docker-compose.yml` или `.env`
2. Убедитесь, что используете правильный параметр: `admin_password`

### Проблемы с подключением к API провайдера

1. Проверьте, что API ключ действителен
2. Убедитесь, что у провайдера достаточно средств/лимита
3. Проверьте сеть и доступность endpoint'а

## Интеграция

### Как интегрировать с существующим проектом?

Просто замените URL и заголовки авторизации:

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

### Как использовать в нескольких проектах?

Создайте отдельный токен для каждого проекта:

```bash
# Проект 1
python create_token.py --provider openai --api-key sk-... --model gpt-4

# Проект 2
python create_token.py --provider anthropic --api-key sk-ant-...
```

Каждый проект будет использовать свой токен, но все запросы будут идти через один IP-адрес.

## Дополнительные возможности

### Как добавить нового провайдера?

Добавьте endpoint в `main.py`:

```python
endpoints = {
    'openai': 'https://api.openai.com/v1/chat/completions',
    'anthropic': 'https://api.anthropic.com/v1/messages',
    'your-provider': 'https://your-provider.com/api/chat'
}
```

И добавьте логику для обработки headers:

```python
if provider == 'your-provider':
    headers['Authorization'] = f'Bearer {api_key}'
    headers['Content-Type'] = 'application/json'
```

### Как добавить rate limiting?

Установите `slowapi`:

```bash
pip install slowapi
```

Добавьте в `main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/v1/chat/completions")
@limiter.limit("10/minute")
async def proxy_completion(...):
    ...
```

## Поддержка

### Где получить помощь?

1. Проверьте этот FAQ
2. Посмотрите логи: `make logs`
3. Проверьте здоровье сервиса: `make health`
4. Изучите примеры в `example_client.py`

### Как сообщить о проблеме?

Создайте issue с описанием:
- Ошибка или неожиданное поведение
- Логи из `docker-compose logs moonproxy`
- Шаги для воспроизведения
- Ваша конфигурация (без секретов!)
