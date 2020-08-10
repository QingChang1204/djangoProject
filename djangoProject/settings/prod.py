from .base import *

try:
    from .local_settings import *
except ImportError:
    DATABASES = DATABASES
else:
    DATABASES = DATABASES_PROD

MIGRATE_APPS = ['blog']

ENV = "prod"

# Seperate Migrations
MIGRATION_MODULES = {app: '%s.prod_migrations' % app for app in MIGRATE_APPS}
