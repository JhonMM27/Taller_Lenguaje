import os
from .base import *

env = os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings.local')

if env == 'config.settings.production':
    from .production import *
else:
    from .local import *