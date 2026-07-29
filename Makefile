.PHONY: help init build up down restart logs ps health test shell clean

help: ## Показать справку
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

init: ## Создать локальный конфиг из шаблона
	@mkdir -p config data logs trace
	@if [ ! -f config/config.yml ]; then cp config/config.example.yml config/config.yml; echo "Создан config/config.yml; внесите Z.ai API key и затем запустите make up."; else echo "config/config.yml уже существует."; fi

build: ## Собрать Moon Bridge image
	docker compose build

up: ## Запустить proxy
	docker compose up -d

down: ## Остановить proxy
	docker compose down

restart: ## Перезапустить proxy
	docker compose restart

logs: ## Показать логи proxy
	docker compose logs -f moonbridge

ps: ## Показать статус контейнера
	docker compose ps

health: ## Проверить валидность активного конфига
	docker compose exec moonbridge /app/moonbridge -config /config/config.yml -print-addr

test: ## Запустить upstream proxy tests
	rm -rf /tmp/moon-bridge-test && git clone --branch main --depth 1 https://github.com/ZhiYi-R/moon-bridge.git /tmp/moon-bridge-test && cd /tmp/moon-bridge-test && go test ./internal/service/proxy

shell: ## Запустить разовую команду Moon Bridge в контейнере
	docker compose exec moonbridge /app/moonbridge -config /config/config.yml -print-mode

clean: ## Остановить контейнеры (локальные config и данные сохраняются)
	docker compose down --rmi local
