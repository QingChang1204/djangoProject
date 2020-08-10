from .base import *

try:
    from .local_settings import *
except ImportError:
    DATABASES = DATABASES
else:
    DATABASES = DATABASES_DEV

MIGRATE_APPS = ['blog']

ENV = "dev"
# Seperate Migrations
MIGRATION_MODULES = {app: '%s.dev_migrations' % app for app in MIGRATE_APPS}
