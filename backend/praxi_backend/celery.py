import os
from celery import Celery

# Default to modular dev settings. Deployments should set DJANGO_SETTINGS_MODULE.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "praxi_backend.settings.dev")

app = Celery("praxi_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()