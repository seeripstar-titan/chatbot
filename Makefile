.PHONY: help install dev seed run test lint docker-up docker-down widget-build widget-dev

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -e ".[dev]"
	cd widget && npm install

dev: ## Run the API server in development mode
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

seed: ## Seed the database with sample data
	python -m backend.seed

run: ## Run the API server in production mode
	uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

test: ## Run tests
	pytest tests/ -v

lint: ## Run linter
	ruff check backend/
	ruff format backend/ --check

format: ## Auto-format code
	ruff check backend/ --fix
	ruff format backend/

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create msg="description")
	alembic revision --autogenerate -m "$(msg)"

widget-build: ## Build the chat widget
	cd widget && npm run build

widget-dev: ## Run widget dev server
	cd widget && npm run dev

docker-up: ## Start all services with Docker Compose
	docker compose up -d --build

docker-down: ## Stop all Docker services
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f api

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage dist build *.egg-info
