# your_project_name/celery.py
import os
from celery import Celery

# Establece el módulo de configuración por defecto de Django para Celery.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PsysMsql.settings')

app = Celery('PsysMsql')

# Usa la configuración de Django para Celery.
# Esto significa que toda la configuración relacionada con Celery la pondrás en settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubre tareas de todas las apps registradas en INSTALLED_APPS.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')