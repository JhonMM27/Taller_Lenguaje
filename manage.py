import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    from django.core.management import execute_from_command_line
except ImportError as exc:
    raise ImportError(
        "Couldn't import Django. Are you sure it's installed?"
    ) from exc

execute_from_command_line(sys.argv)