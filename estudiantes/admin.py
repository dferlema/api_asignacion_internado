# ============================================================
# ADMIN.PY — App Estudiantes
# Configura el panel de administración de Django para
# gestionar estudiantes directamente desde /admin/
# ============================================================

from django.contrib import admin
from .models import Estudiante


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    """
    Panel admin para gestión de estudiantes.
    Accesible desde: http://localhost:8000/admin/estudiantes/estudiante/
    """

    # Columnas visibles en el listado
    list_display = [
        'cedula',
        'apellidos',
        'nombres',
        'calificaciones',
        'cargas_familiares',
        'situacion_economica',
        'modulos_ingles_aprobados',
        'calificaciones_cerradas',
        'status',                   # Campo de ModelBase (activo/inactivo)
    ]

    # Filtros en la barra lateral derecha
    list_filter = [
        'estado_civil',
        'ubicacion_geografica',
        'situacion_economica',
        'modulos_ingles_aprobados',
        'calificaciones_cerradas',
        'status',
    ]

    # Campos por los que se puede buscar
    search_fields = ['cedula', 'nombres', 'apellidos', 'correo']

    # Ordenamiento por defecto
    ordering = ['-date_create']

    # Campos de solo lectura (vienen de ModelBase)
    readonly_fields = [
        'date_create',
        'date_modification',
        'user_create',
        'user_modification',
        'ip_create',
        'ip_modification',
        'date_delete',
        'user_delete',
        'ip_delete',
    ]

    # Organización de campos en el formulario de detalle
    fieldsets = (
        ('Datos Personales', {
            'fields': ('cedula', 'nombres', 'apellidos', 'correo', 'telefono')
        }),
        ('Variables para el Ranking IA', {
            'fields': (
                'estado_civil', 'cargas_familiares',
                'ubicacion_geografica', 'situacion_economica',
                'calificaciones', 'nivel_academico',
            )
        }),
        ('Requisitos Habilitantes', {
            'fields': ('modulos_ingles_aprobados', 'calificaciones_cerradas')
        }),
        ('Auditoría (ModelBase)', {
            'classes': ('collapse',),   # Se muestra colapsado por defecto
            'fields': (
                'status',
                'date_create', 'user_create', 'ip_create',
                'date_modification', 'user_modification', 'ip_modification',
                'date_delete', 'user_delete', 'ip_delete',
            )
        }),
    )
