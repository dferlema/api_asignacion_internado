#!/usr/bin/env python
# ============================================================
# MANAGE.PY — Comandos de administración de Django
#
# Comandos más usados:
#   python manage.py runserver          → iniciar servidor
#   python manage.py makemigrations     → generar migraciones
#   python manage.py migrate            → aplicar migraciones
#   python manage.py createsuperuser    → crear administrador
#   python manage.py shell              → consola interactiva
# ============================================================

import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'internado.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'No se pudo importar Django. Verifica que esté instalado '
            'y activo en tu entorno virtual (venv).'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
