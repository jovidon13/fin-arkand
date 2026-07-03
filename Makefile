.PHONY: help up down logs seed migrate test lint backend frontend

help:
	@echo "ARKAND Finance — commands:"
	@echo "  make up        — docker compose up (full stack)"
	@echo "  make down      — stop the stack"
	@echo "  make logs      — tail logs"
	@echo "  make migrate   — run backend migrations (in container)"
	@echo "  make seed      — seed demo data (in container)"
	@echo "  make test      — run backend test suite (sqlite)"
	@echo "  make lint      — ruff (backend) + tsc (frontend)"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

migrate:
	docker compose exec backend python manage.py migrate

seed:
	docker compose exec backend python manage.py seed_demo --reset

test:
	cd backend && USE_SQLITE=1 python -m pytest -q

lint:
	cd backend && ruff check apps/
	cd frontend && npm run typecheck
