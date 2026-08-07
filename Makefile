.PHONY: tests

DOCKER_WEB := docker compose exec web
UV_RUN := uv run
UV_ADD := uv add
EXEC_IN_WEB := $(DOCKER_WEB) $(UV_RUN)
MANAGE_PY := python manage.py

check-django:
	$(EXEC_IN_WEB) $(MANAGE_PY) check

migrations:
	$(EXEC_IN_WEB) $(MANAGE_PY) makemigrations

migrate:
	$(EXEC_IN_WEB) $(MANAGE_PY) migrate

linter:
	$(UV_RUN) ruff check .

linter-fix:
	$(UV_RUN) ruff check . --fix
	$(UV_RUN) ruff format .

tests:
	$(EXEC_IN_WEB) pytest -v

dep-add:
	$(DOCKER_WEB) $(UV_ADD) $(filter-out $@,$(MAKECMDGOALS))
	$(UV_ADD) $(filter-out $@,$(MAKECMDGOALS))

depdev-add:
	$(DOCKER_WEB) $(UV_ADD) $(filter-out $@,$(MAKECMDGOALS)) --dev
	$(UV_ADD) $(filter-out $@,$(MAKECMDGOALS)) --dev

%:
	@:
