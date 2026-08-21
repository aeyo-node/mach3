.PHONY: setup up down logs test lint migrate seed health replay clean

setup:
	cp -n .env.example .env || true
	pip install -e ".[dev]"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	pytest tests/ -v

lint:
	ruff check .

format:
	ruff format .

migrate:
	alembic upgrade head

seed:
	python -m swaram.storage.seed

health:
	curl -s http://localhost:8000/health | jq .
	curl -s http://localhost:8000/health/providers | jq .

replay:
	python -m swaram.replay --symbol CRYPTO:BTC/USD

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -r {} +
