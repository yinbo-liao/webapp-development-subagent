.PHONY: help install test lint format scan pre-commit demo clean

help:
	@echo "Enterprise Web Development System v2.0"
	@echo ""
	@echo "Available targets:"
	@echo "  install       Install system dependencies"
	@echo "  test          Run test suite"
	@echo "  lint          Run linters (flake8 + mypy + bandit)"
	@echo "  format        Format code (black + isort)"
	@echo "  scan          Run full ECC scan on project"
	@echo "  pre-commit    Run ECC pre-commit check (blocks on critical/high)"
	@echo "  scan-file     Run ECC scan on a single file (usage: make scan-file FILE=path/to/file.py)"
	@echo "  demo          Run demo workflow"
	@echo "  clean         Clean generated files and caches"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest app/tests --cov=app --cov-report=term-missing

lint:
	flake8 agents ecc_tools shared --max-line-length=100
	mypy agents ecc_tools shared --ignore-missing-imports
	bandit -r agents ecc_tools shared -f json -o bandit-report.json

format:
	black agents ecc_tools shared --line-length=100
	isort agents ecc_tools shared --profile=black

scan:
	python main.py --ecc-scan --project . --output html

pre-commit:
	python main.py --ecc-scan --pre-commit --project .

scan-file:
	python main.py --ecc-scan --file $(FILE) --output json

demo:
	python demo.py

clean:
	rm -rf demo-output/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "bandit-report.json" -delete
