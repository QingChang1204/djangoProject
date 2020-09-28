import os
from django.conf import settings
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings.prod')
app = Celery('djangoProject')

app.config_from_object('django.conf:settings', namespace="CELERY")
app.autodiscover_tasks(lambda: settings.CUSTOM_APPS)


class Router:

    @staticmethod
    def route_for_task(name, args=None, kwargs=None):
        if name.startswith('blog_daily'):
            return settings.DAILY_QUEUE
        if name.startswith('blog_signal'):
            return settings.SIGNAL_QUEUE
        else:
            return settings.DEFAULT_QUEUE


app.conf.update(
    {"task_routes": Router()}
)
