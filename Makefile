.PHONY: tests

DOCKER_WEB := docker compose exec web
UV := uv run
EXEC_IN_WEB := $(DOCKER_WEB) $(UV)
MANAGE_PY := python manage.py

check-django:
	$(EXEC_IN_WEB) $(MANAGE_PY) check

migrations:
	$(EXEC_IN_WEB) $(MANAGE_PY) makemigrations

migrate:
	$(EXEC_IN_WEB) $(MANAGE_PY) migrate

linter:
	$(UV) ruff check .

linter-fix:
	$(UV) ruff check . --fix
	$(UV) ruff format .

tests:
	$(EXEC_IN_WEB) pytest apps/accounts/tests -v
