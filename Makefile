# Makefile для Barkery_bot

.PHONY: help install test test-all test-models test-services clean

help:
	@echo "🐶 Barkery Bot - Команды для разработки"
	@echo ""
	@echo "Установка:"
	@echo "  make install        - Установить все зависимости"
	@echo "  make install-dev    - Установить только dev зависимости"
	@echo ""
	@echo "Тестирование:"
	@echo "  make test           - Запустить все тесты"
	@echo "  make test-models    - Тесты моделей БД"
	@echo "  make test-services  - Тесты сервисов"
	@echo ""
	@echo "Разработка:"
	@echo "  make clean          - Очистить кэш и временные файлы"
	@echo "  make run            - Запустить бота"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	python run_tests.py

test-models:
	python run_tests.py tests/test_models.py

test-services:
	python run_tests.py tests/test_services_simple.py

run:
	python start_bot.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null