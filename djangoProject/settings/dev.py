from .base import *

try:
    from .local_settings import *
except ImportError:
    DATABASES = DATABASES
else:
    DATABASES = DATABASES_DEV
    CACHES = CACHES_DEV


# Separate Migrations
MIGRATION_MODULES = {app: '%s.dev_migrations' % app for app in MIGRATE_APPS}
