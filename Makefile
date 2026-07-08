DOCKER_WEB := docker compose exec web
UV := uv run
EXEC_IN_WEB := $(DOCKER_WEB) $(UV)
MANAGE_PY := python manage.py

check-django:
	$(EXEC_IN_WEB) $(MANAGE_PY) check

makemigrations:
	$(EXEC_IN_WEB) $(MANAGE_PY) makemigrations

migrate:
	$(EXEC_IN_WEB) $(MANAGE_PY) migrate

linter:
	uv run ruff check .
	uv run ruff format --check .