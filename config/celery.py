import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('medicine-platform-exp')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.update(
    control_queue_exclusive=True,
    event_queue_exclusive=True,
)
app.autodiscover_tasks()
