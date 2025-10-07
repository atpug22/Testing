# FastAPI Boilerplate Makefile

.PHONY: help format lint test clean install dev-setup

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

format: ## Format code with Black and isort
	@echo "🎨 Formatting code..."
	python format_code.py

lint: ## Run linting checks
	@echo "🔍 Running linting checks..."
	flake8 app/ api/ core/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	mypy app/ api/ core/ --ignore-missing-imports

test: ## Run tests
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-ai: ## Run AI integration tests
	@echo "🤖 Running AI integration tests..."
	python test_enhanced_ai.py

install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	poetry install

dev-setup: ## Set up development environment
	@echo "🛠️ Setting up development environment..."
	poetry install
	pre-commit install
	@echo "✅ Development environment ready!"

clean: ## Clean up temporary files
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	poetry run alembic upgrade head

reset-db: ## Reset database
	@echo "🔄 Resetting database..."
	poetry run alembic downgrade base
	poetry run alembic upgrade head

start: ## Start the development server
	@echo "🚀 Starting development server..."
	python main.py

# AI-specific commands
ai-test: ## Test AI endpoints
	@echo "🤖 Testing AI endpoints..."
	curl -s http://localhost:8000/v1/ai/health | jq .
	curl -s http://localhost:8000/v1/ai/analytics | jq .
	curl -s http://localhost:8000/v1/ai/usage-metrics | jq .

ai-docs: ## Open AI API documentation
	@echo "📚 Opening AI API documentation..."
	@echo "Visit: http://localhost:8000/docs"

# Formatting shortcuts
black: ## Run Black formatter
	black app/ api/ core/ tests/ main.py format_code.py test_enhanced_ai.py

isort: ## Run isort import sorter
	isort --profile=black --multi-line=3 app/ api/ core/ tests/ main.py format_code.py test_enhanced_ai.py

check-format: ## Check if code is properly formatted
	@echo "🔍 Checking code formatting..."
	black --check app/ api/ core/ tests/ main.py format_code.py test_enhanced_ai.py
	isort --check-only --profile=black app/ api/ core/ tests/ main.py format_code.py test_enhanced_ai.py
	@echo "✅ Code formatting is correct!"

pre-commit-all: ## Run pre-commit on all files
	@echo "🔧 Running pre-commit on all files..."
	pre-commit run --all-files
