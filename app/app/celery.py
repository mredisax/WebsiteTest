from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab
import time


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')
app = Celery("app")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.timezone = 'Europe/Warsaw'


app.conf.ONCE = {
  'backend': 'celery_once.backends.Redis',
  'settings': {
    'url': 'redis://redis:6379/0',
    'default_timeout': 60 * 60
  }
}

app.conf.update(
    result_backend='django-db',
)
app.autodiscover_tasks()

# app.conf.beat_schedule = {
#  "everyday-task": {
#  "task": "app.cron_check_ip",
#  "schedule": crontab(minute="*/1")
# #  hour="*/1"
#  }
# }