from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

from deadline.settings import RABBITMQ_CLIENT

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deadline.settings')

app = Celery('Deadline')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@app.task
def send_notification(notification_id):
    """
    A task to asynchronously send a notification message to RabbitMQ
    """
    RABBITMQ_CLIENT.send_notification_message(notification_id)
