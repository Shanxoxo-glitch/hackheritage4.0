.PHONY: help up down restart logs test test-scoring clean

help:
	@echo "SIH 2026 PS 26094 Stack Management"
	@echo "  make up      - Spin up entire docker stack"
	@echo "  make down    - Stop and remove all containers"
	@echo "  make logs    - Tail container logs"
	@echo "  make test    - Run test suite for backend"
	@echo "  make test-scoring - Run scoring contract tests (mocked models)"

up:
	docker compose up -d --build

down:
	docker compose down --volumes

logs:
	docker compose logs -f

test:
	cd services/backend && python -m pytest tests/ -v

test-scoring:
	cd services/scoring && PYTHONPATH=. SCORING_WARM_ON_START=0 python -m pytest tests/ -v

clean:
	docker compose down --rmi all --volumes
