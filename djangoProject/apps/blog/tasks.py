from __future__ import absolute_import, unicode_literals
from blog.utils import logger
from djangoProject.celery import app as celery_app


@celery_app.task
def async_test():
    logger.info(1111)
