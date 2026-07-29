.PHONY: help build up down restart logs clean install test

help: ## Показать эту справку
	@echo "MoonProxy Docker - Команды управления"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Собрать Docker образ
	docker-compose build

up: ## Запустить сервисы
	docker-compose up -d

down: ## Остановить сервисы
	docker-compose down

restart: ## Перезапустить сервисы
	docker-compose restart

logs: ## Показать логи сервисов
	docker-compose logs -f moonproxy

clean: ## Остановить и удалить контейнеры, сети и образы
	docker-compose down -v --rmi all

install: ## Установить зависимости локально
	pip install -r requirements.txt

test: ## Запустить тесты
	python -m pytest tests/

dev: ## Запустить в режиме разработки
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

shell: ## Открыть shell в контейнере
	docker-compose exec moonproxy /bin/bash

ps: ## Показать статус контейнеров
	docker-compose ps

health: ## Проверить здоровье сервиса
	curl -f http://localhost:8000/health || echo "Service is not healthy"

init: ## Инициализация проекта
	@mkdir -p data config
	@echo "Директории созданы"
	@echo "Скопируйте .env.example в .env и настройте переменные окружения"
