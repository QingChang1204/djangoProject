from .base import *

try:
    from .local_settings import *
except ImportError:
    DATABASES = DATABASES
else:
    DATABASES = DATABASES_PROD
    CACHES = CACHES_PROD
    CELERY_BROKER_URL = BROKER_URL_PROD
    CELERY_RESULT_BACKEND = CELERY_RESULT_BACKEND_PROD


# Separate Migrations
MIGRATION_MODULES = {app: '%s.prod_migrations' % app for app in MIGRATE_APPS}
