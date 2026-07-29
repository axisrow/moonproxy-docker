#!/bin/bash

# MoonProxy - Скрипт быстрого старта
# Этот скрипт автоматически настраивает и запускает MoonProxy

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           MoonProxy - Быстрый старт                         ║"
    echo "║     Сервис для проксирования LLM API с управлением токенами ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Проверка зависимостей
check_dependencies() {
    print_info "Проверка зависимостей..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен. Установите Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose не установлен. Установите Docker Compose"
        exit 1
    fi

    print_success "Все зависимости установлены"
}

# Создание структуры директорий
setup_directories() {
    print_info "Создание структуры директорий..."

    mkdir -p data config logs

    print_success "Структура директорий создана"
}

# Настройка переменных окружения
setup_environment() {
    print_info "Настройка переменных окружения..."

    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env

            # Генерация безопасного секретного ключа
            SECRET_KEY=$(openssl rand -hex 32)
            ADMIN_PASSWORD=$(openssl rand -base64 12)

            # Обновление .env файла
            sed -i.bak "s/your-secret-key-change-this/$SECRET_KEY/" .env
            sed -i.bak "s/admin123/$ADMIN_PASSWORD/" .env
            rm -f .env.bak

            print_success "Файл .env создан"
            print_warning "Ваш новый админ пароль: $ADMIN_PASSWORD"
            print_warning "Сохраните его, он понадобится для создания токенов!"

            # Сохранение пароля в файл
            echo "$ADMIN_PASSWORD" > .admin_password
            chmod 600 .admin_password
        else
            print_warning "Файл .env.example не найден, используем дефолтные настройки"
        fi
    else
        print_success "Файл .env уже существует"
    fi
}

# Сборка и запуск Docker контейнеров
build_and_start() {
    print_info "Сборка Docker образа..."

    if command -v docker-compose &> /dev/null; then
        docker-compose build
    else
        docker compose build
    fi

    print_success "Docker образ собран"

    print_info "Запуск сервисов..."

    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi

    print_success "Сервисы запущены"
}

# Ожидание запуска сервиса
wait_for_service() {
    print_info "Ожидание запуска сервиса..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Сервис запущен и готов к работе!"
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo ""
    print_error "Сервис не запустился за отведённое время"
    return 1
}

# Проверка здоровья сервиса
health_check() {
    print_info "Проверка здоровья сервиса..."

    response=$(curl -s http://localhost:8000/health)

    if [ $? -eq 0 ]; then
        print_success "Сервис здоров!"
        echo "Ответ: $response"
    else
        print_error "Сервис не отвечает"
        return 1
    fi
}

# Показ информации о следующих шагах
show_next_steps() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   🎉 MoonProxy готов к использованию!       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo "📋 Следующие шаги:"
    echo ""
    echo "1. 📝 Создайте ваш первый токен:"
    echo "   python create_token.py --provider openai --api-key sk-... --model gpt-4"
    echo ""
    echo "2. 🧪 Протестируйте сервис:"
    echo "   python test_moonproxy.py"
    echo ""
    echo "3. 📚 Посмотрите примеры использования:"
    echo "   python example_client.py"
    echo ""
    echo "4. 📖 Документация:"
    echo "   cat README.md"
    echo "   cat FAQ.md"
    echo ""
    echo "🔧 Полезные команды:"
    echo "   make logs          - Посмотреть логи"
    echo "   make restart       - Перезапустить сервис"
    echo "   make down          - Остановить сервис"
    echo "   make help          - Показать все команды"
    echo ""

    if [ -f .admin_password ]; then
        ADMIN_PASS=$(cat .admin_password)
        echo -e "${YELLOW}🔑 Ваш админ пароль: $ADMIN_PASS${NC}"
        echo -e "${YELLOW}   Он сохранён в файле .admin_password${NC}"
        echo ""
    fi

    echo "📍 URL сервиса: http://localhost:8000"
    echo "📍 Health check: http://localhost:8000/health"
    echo ""
}

# Основная функция
main() {
    print_header

    check_dependencies
    setup_directories
    setup_environment
    build_and_start

    if wait_for_service; then
        health_check
        show_next_steps
        exit 0
    else
        print_error "Не удалось запустить сервис"
        echo ""
        echo "Проверьте логи:"
        echo "  docker-compose logs moonproxy"
        echo ""
        exit 1
    fi
}

# Запуск
main "$@"
