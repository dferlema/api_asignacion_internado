# ============================================================
# WSGI.PY — Punto de entrada para servidores en producción
# ============================================================

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'internado.settings')
application = get_wsgi_application()
