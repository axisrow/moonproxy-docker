# 🚀 MoonProxy - Руководство по развёртыванию в продакшене

Это подробное руководство по безопасному развёртыванию MoonProxy в production среде.

## 📋 Подготовка

### Системные требования

- **Docker**: версии 20.10 или выше
- **Docker Compose**: версии 2.0 или выше
- **CPU**: минимум 1 ядро
- **RAM**: минимум 512 MB
- **Disk**: минимум 1 GB свободного места

### Необходимое программное обеспечение

```bash
# Установка Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🔐 Безопасность

### 1. Генерация безопасных ключей

```bash
# Генерация секретного ключа (32 байта = 64 hex символа)
openssl rand -hex 32

# Генерация админ пароля (16 символов)
openssl rand -base64 16
```

### 2. Настройка переменных окружения

Создайте файл `.env` в директории проекта:

```bash
# Секретный ключ для JWT токенов (обязателен, измените!)
MOONPROXY_SECRET_KEY=your-generated-secret-key-here

# Админ пароль (обязателен, измените!)
MOONPROXY_ADMIN_PASSWORD=your-generated-admin-password-here

# Уровень логирования
MOONPROXY_LOG_LEVEL=INFO

# Порт сервиса
MOONPROXY_PORT=8000

# Хост для привязки
MOONPROXY_HOST=0.0.0.0
```

### 3. Права доступа к файлам

```bash
# Установка безопасных прав для .env файла
chmod 600 .env

# Права для директории с данными
chmod 700 data/
```

## 🌐 Настройка Reverse Proxy

### Вариант 1: Caddy (автоматический HTTPS)

**Установка Caddy:**

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

**Конфигурация Caddy:**

Отредактируйте `/etc/caddy/Caddyfile`:

```
moonproxy.yourdomain.com {
    reverse_proxy localhost:8000

    # Логирование
    log {
        output file /var/log/caddy/moonproxy.log
        format json
    }

    # Ограничение скорости (опционально)
    limit_rate 512k
}

# Перенаправление HTTP на HTTPS
http://moonproxy.yourdomain.com {
    redir https://moonproxy.yourdomain.com{uri}
}
```

**Перезапуск Caddy:**

```bash
sudo systemctl restart caddy
sudo systemctl enable caddy
```

### Вариант 2: Nginx

**Установка Nginx:**

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

**Конфигурация Nginx:**

Создайте файл `/etc/nginx/sites-available/moonproxy`:

```nginx
server {
    listen 80;
    server_name moonproxy.yourdomain.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name moonproxy.yourdomain.com;

    # SSL сертификаты (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/moonproxy.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/moonproxy.yourdomain.com/privkey.pem;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Логирование
    access_log /var/log/nginx/moonproxy_access.log;
    error_log /var/log/nginx/moonproxy_error.log;

    # Reverse proxy
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Ограничение размера запроса
    client_max_body_size 10M;
}
```

**Получение SSL сертификата:**

```bash
sudo certbot --nginx -d moonproxy.yourdomain.com
```

**Активация конфигурации:**

```bash
sudo ln -s /etc/nginx/sites-available/moonproxy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🛡️ Firewall

### Настройка UFW (Ubuntu)

```bash
# Разрешить SSH
sudo ufw allow 22/tcp

# Разрешить HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Ограничить доступ к MoonProxy по IP (опционально)
sudo ufw allow from YOUR_IP_ADDRESS to any port 8000 proto tcp

# Включить firewall
sudo ufw enable
sudo ufw status
```

## 🚀 Развёртывание

### 1. Клонирование или копирование файлов

```bash
# Клонирование репозитория (если применимо)
git clone your-repo-url
cd moonproxy_docker

# Или копирование файлов на сервер
scp -r moonproxy_docker/ user@server:/path/to/destination/
```

### 2. Настройка окружения

```bash
# Создание .env файла
cp .env.example .env

# Редактирование с безопасными значениями
nano .env
```

### 3. Создание директорий

```bash
mkdir -p data config logs
chmod 700 data config logs
```

### 4. Запуск сервиса

```bash
# Сборка образа
docker-compose build

# Запуск в фоновом режиме
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### 5. Проверка работоспособности

```bash
# Health check
curl http://localhost:8000/health

# Проверка через reverse proxy
curl https://moonproxy.yourdomain.com/health
```

## 📊 Мониторинг

### Systemd сервис для автозапуска

Создайте файл `/etc/systemd/system/moonproxy.service`:

```ini
[Unit]
Description=MoonProxy Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/moonproxy_docker
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

**Активация сервиса:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable moonproxy
sudo systemctl start moonproxy
sudo systemctl status moonproxy
```

### Логирование

```bash
# Просмотр логов
docker-compose logs -f moonproxy

# Проверка ошибок
docker-compose logs moonproxy | grep ERROR

# Логи за последние 100 строк
docker-compose logs --tail=100 moonproxy
```

### Мониторинг ресурсов

```bash
# Статистика контейнера
docker stats moonproxy

# Использование диска
docker system df
```

## 💾 Резервное копирование

### Автоматическое резервирование

Создайте скрипт `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups/moonproxy"
DATA_DIR="/path/to/moonproxy_docker/data"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Резервное копирование данных
tar -czf $BACKUP_DIR/moonproxy_$DATE.tar.gz $DATA_DIR

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "moonproxy_*.tar.gz" -mtime +30 -delete

echo "Backup completed: moonproxy_$DATE.tar.gz"
```

**Добавление в cron:**

```bash
# Ежедневное резервирование в 2:00 ночи
crontab -e
0 2 * * * /path/to/backup.sh
```

## 🔄 Обновление

### Безопасное обновление

```bash
# 1. Резервное копирование
./backup.sh

# 2. Остановка сервиса
docker-compose down

# 3. Обновление кода
git pull

# 4. Обновление зависимостей (если нужно)
docker-compose build --no-cache

# 5. Запуск обновлённого сервиса
docker-compose up -d

# 6. Проверка
docker-compose ps
curl http://localhost:8000/health
```

## 🔧 Оптимизация

### Настройка ресурсов

Отредактируйте `docker-compose.yml`:

```yaml
services:
  moonproxy:
    # ... другие настройки ...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Rate limiting

Добавьте в `main.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/v1/chat/completions")
@limiter.limit("10/minute")
async def proxy_completion(...):
    ...
```

## 🚨 troubleshooting

### Проблемы с памятью

```bash
# Ограничение логов
docker-compose down
docker system prune -a
docker-compose up -d
```

### Проблемы с сетью

```bash
# Проверка портов
sudo netstat -tulpn | grep 8000

# Проверка firewall
sudo ufw status
```

### Проверка SSL сертификатов

```bash
# Проверка срока действия
sudo certbot certificates

# Обновление сертификатов
sudo certbot renew
```

## 📋 Чеклист перед продакшеном

- [ ] Изменены все дефолтные пароли и ключи
- [ ] Настроен HTTPS с валидным SSL сертификатом
- [ ] Настроен firewall
- [ ] Ограничен доступ к API (по IP или авторизации)
- [ ] Настроено резервное копирование
- [ ] Настроен автоматический запуск (systemd)
- [ ] Проверены логи и мониторинг
- [ ] Протестировано обновление
- [ ] Настроены алерты при проблемах
- [ ] Документированы процедуры восстановления

## 🎯 После развёртывания

1. **Создайте первый токен** и протестируйте работу
2. **Настройте мониторинг** (Prometheus, Grafana, или простые health checks)
3. **Установите алерты** при проблемах с сервисом
4. **Документируйте** процедуры эксплуатации
5. **Регулярно тестируйте** восстановление из бэкапов

---

**После развёртывания вы получите безопасный, надёжный сервис для управления LLM API!** 🎉
