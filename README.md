[![Quality gate status](https://sonarcloud.io/api/project_badges/measure?project=maryaniskina_medicine-platform-exp&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=maryaniskina_medicine-platform-exp)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=maryaniskina_medicine-platform-exp&metric=coverage)](https://sonarcloud.io/summary/new_code?id=maryaniskina_medicine-platform-exp)
[![CI](https://github.com/maryaniskina/medicine-platform-exp/actions/workflows/ci.yml/badge.svg)](https://github.com/maryaniskina/medicine-platform-exp/actions/workflows/ci.yml)

# MedBook

MedBook — API-платформа для записи пациентов на приём к врачам. Проект поддерживает работу с клиниками, врачами, расписанием, записями на приём и уведомлениями.

## Стек

- Python 3.13
- Django 6.1 и Django REST Framework
- PostgreSQL
- RabbitMQ — обмен событиями с внешними системами
- Redis — кеширование и backend для Celery
- Celery и Celery Beat — фоновые задачи и периодические уведомления
- drf-spectacular — OpenAPI, Swagger UI и ReDoc
- Docker Compose
- pytest, pytest-django, pytest-cov, Ruff
- GitHub Actions и SonarCloud

## Возможности

- Регистрация, вход, выход и получение данных текущего пользователя.
- Просмотр клиник, врачей и специализаций.
- Получение доступных временных слотов по расписанию врача.
- Создание, просмотр и отмена записей на приём.
- Разделение записей пациента и врача.
- Уведомления о записи, отмене и предстоящем приёме.
- Получение списка уведомлений, счётчика непрочитанных и отметка о прочтении.
- Приём событий о клиниках и врачах через RabbitMQ.
- Повторная обработка временно неуспешных событий и отправка постоянных ошибок в dead-letter queue.
- Проверка работоспособности сервиса через health endpoint.
- Автоматические проверки линтером и тестами в CI.

## Запуск через Docker Compose

1. Создайте файл `.env` на основе `.env.example` и при необходимости измените
   параметры подключения и секретный ключ Django.
2. Запустите сервисы:

   ```bash
   docker compose up --build
   ```

Compose поднимет PostgreSQL, Redis, RabbitMQ, Django, Celery worker,
Celery Beat и consumer событий. Миграции выполняются отдельным сервисом
перед запуском веб-приложения.

После запуска доступны:

- API: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI-схема: `http://127.0.0.1:8000/api/schema/`
- Health check: `http://127.0.0.1:8000/health/`
- RabbitMQ Management: `http://127.0.0.1:15672/`

Порты и учётные данные локального окружения задаются в `docker-compose.yml`
и `.env.example`. Для не локального развёртывания обязательно задайте
собственные секреты и пароли.

## Основные API-маршруты

| Раздел | Префикс | Назначение |
|---|---|---|
| Аккаунты | `/api/accounts/` | Регистрация, вход, выход, профиль и CSRF |
| Клиники | `/api/clinics/` | Список клиник и карточка клиники |
| Врачи | `/api/doctors/` | Список врачей, карточка врача и специализации |
| Расписание | `/api/scheduling/` | Доступные слоты для записи |
| Записи | `/api/appointments/` | Создание, просмотр и отмена записей |
| Уведомления | `/api/notifications/` | Список, счётчик и прочтение уведомлений |

Подробная схема запросов и ответов доступна в Swagger UI и ReDoc.

## Разработка

Зависимости проекта управляются через `uv`.

Установить зависимости, включая группы разработки:

```bash
uv sync --all-groups
```

Проверить Django:

```bash
uv run python manage.py check
```

Создать миграции и применить их:

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

Запустить тесты:

```bash
uv run pytest -v
```

Запустить тесты с отчётом о покрытии:

```bash
uv run pytest -v --cov=apps --cov=common --cov=config --cov-report=term-missing
```

Проверить стиль и форматирование:

```bash
uv run ruff check .
uv run ruff format --check .
```

В проекте также доступны соответствующие команды Makefile, например `make tests`,
`make linter`, `make linter-fix`, `make check-django` и `make migrate`.

## Реализовать

- [x] Пользовательская модель и API аккаунтов
- [x] Регистрация, вход и выход с CSRF-защитой
- [x] API клиник
- [x] Получение клиник из RabbitMQ
- [x] API врачей и специализаций
- [x] Получение событий о врачах через RabbitMQ
- [x] Повторная обработка событий и dead-letter queue
- [x] Расписание врачей и поиск доступных слотов
- [x] Создание, просмотр и отмена записей на приём
- [x] Проверки конфликтов активных записей на один слот
- [x] Уведомления о записи и отмене
- [x] Периодические напоминания о предстоящих приёмах через Celery
- [x] API уведомлений и отметка о прочтении
- [x] Docker Compose для сервисов приложения
- [x] Тесты для основных приложений
- [x] Ruff: проверка стиля и форматирования
- [x] GitHub Actions: CI с тестами и проверками
- [x] SonarCloud: анализ качества и покрытия
- [x] Swagger UI, ReDoc и OpenAPI-схема
