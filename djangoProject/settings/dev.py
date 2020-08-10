from .base import *

try:
    from .local_settings import *
except ImportError:
    DATABASES = DATABASES
    CACHES['default']['LOCATION'] = CASH_URL_DEV
else:
    DATABASES = DATABASES_DEV


# Separate Migrations
MIGRATION_MODULES = {app: '%s.dev_migrations' % app for app in MIGRATE_APPS}
