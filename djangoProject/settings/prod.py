from .base import *

try:
    from .local_settings import *
except ImportError:
    DATABASES = DATABASES
    CACHES['default']['LOCATION'] = CASH_URL_PROD
else:
    DATABASES = DATABASES_PROD


# Separate Migrations
MIGRATION_MODULES = {app: '%s.prod_migrations' % app for app in MIGRATE_APPS}
