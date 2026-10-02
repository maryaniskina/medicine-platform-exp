from django.apps import AppConfig


class DoctorsConfig(AppConfig):
    name = 'apps.doctors'

    def ready(self):
        import apps.doctors.signals  # noqa: F401
