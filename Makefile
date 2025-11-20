.PHONY: help install install-dev lint format type-check security test test-cov clean validate assess coverage complexity dead-code improve all

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

lint:  ## Run linting checks
	@echo "Running ruff linter..."
	ruff check .

lint-fix:  ## Run linting checks and auto-fix issues
	@echo "Running ruff linter with auto-fix..."
	ruff check --fix .

format:  ## Format code with ruff
	@echo "Formatting code with ruff..."
	ruff format .

format-check:  ## Check code formatting without making changes
	@echo "Checking code formatting..."
	ruff format --check .

type-check:  ## Run type checking with mypy
	@echo "Running mypy type checker..."
	mypy app tests

security:  ## Run security checks with bandit
	@echo "Running bandit security scanner..."
	bandit -c pyproject.toml -r app

test:  ## Run tests
	@echo "Running tests..."
	pytest -v

test-cov:  ## Run tests with coverage report
	@echo "Running tests with coverage..."
	pytest -v --cov=app --cov-report=html --cov-report=term-missing

clean:  ## Clean up generated files
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf htmlcov/ .coverage coverage.xml

validate: lint-fix format type-check security  ## Run all validation checks (with auto-fix)
	@echo "✅ All validation checks passed!"

assess:  ## Run quality assessment and get recommendations
	@python3 scripts/assess_quality.py

coverage:  ## Measure test coverage
	@echo "Measuring test coverage..."
	pytest --cov=app --cov-report=html --cov-report=term-missing
	@echo "\n📊 Open htmlcov/index.html to view detailed report"

complexity:  ## Check code complexity
	@echo "Checking code complexity..."
	@ruff check app/ --select C90 || true

dead-code:  ## Find unused code (requires vulture)
	@echo "Scanning for dead code..."
	@command -v vulture >/dev/null 2>&1 && vulture app/ || echo "Install vulture: pip install vulture"

improve:  ## Auto-fix all safe issues
	@echo "Auto-fixing issues..."
	ruff check app/ --fix --unsafe-fixes
	ruff format app/
	@echo "✅ Auto-fixes applied. Run 'make assess' to see remaining issues."

all: clean install-dev validate test-cov  ## Run complete CI/CD pipeline
	@echo "✅ Complete pipeline finished!"

# Docker commands
docker-build:  ## Build Docker image
	docker-compose build

docker-up:  ## Start all services
	docker-compose up -d

docker-down:  ## Stop all services
	docker-compose down

docker-logs:  ## Show logs from all services
	docker-compose logs -f

docker-clean:  ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all
