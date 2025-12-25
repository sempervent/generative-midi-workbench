.PHONY: docs dev check commit install-hooks version changelog docker-dev docker-prod docker-down docker-logs docker-clean

# Docker Compose Commands
docker-dev:
	docker compose --profile dev up --build

docker-prod:
	docker compose --profile prod up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-clean:
	docker compose down -v
	docker system prune -f

# Documentation
docs:
	mkdocs build --strict

dev:
	mkdocs serve -a 0.0.0.0:8000

check:
	pre-commit run --all-files

install-hooks:
	pre-commit install --hook-type pre-commit --hook-type commit-msg

commit:
	cz commit

version:
	cz bump --check-consistency

changelog:
	cz changelog

