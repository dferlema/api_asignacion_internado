# ============================================================
# ADMIN.PY — App Plazas
# Configura el panel de administración de Django para
# gestionar plazas y asignaciones desde /admin/
# ============================================================

from django.contrib import admin
from .models import PlazaInternado, AsignacionPlaza


@admin.register(PlazaInternado)
class PlazaInternadoAdmin(admin.ModelAdmin):
    """
    Panel admin para gestión de plazas de internado.
    Accesible desde: http://localhost:8000/admin/plazas/plazainternado/
    """

    list_display = [
        'codigo',
        'institucion',
        'area',
        'ciudad',
        'estado',
        'periodo',
        'status',
    ]

    list_filter  = ['estado', 'area', 'ciudad', 'periodo', 'status']
    search_fields = ['codigo', 'institucion', 'ciudad']
    ordering      = ['institucion', 'area']

    readonly_fields = [
        'date_create', 'user_create', 'ip_create',
        'date_modification', 'user_modification', 'ip_modification',
        'date_delete', 'user_delete', 'ip_delete',
    ]

    fieldsets = (
        ('Datos de la Plaza', {
            'fields': ('codigo', 'institucion', 'area', 'ciudad', 'direccion')
        }),
        ('Estado y Período', {
            'fields': ('estado', 'periodo')
        }),
        ('Auditoría (ModelBase)', {
            'classes': ('collapse',),
            'fields': (
                'status',
                'date_create', 'user_create', 'ip_create',
                'date_modification', 'user_modification', 'ip_modification',
                'date_delete', 'user_delete', 'ip_delete',
            )
        }),
    )


@admin.register(AsignacionPlaza)
class AsignacionPlazaAdmin(admin.ModelAdmin):
    """
    Panel admin para consultar asignaciones de plazas.
    Solo lectura — las asignaciones se crean desde el endpoint
    POST /api/v1/ranking/asignar/
    Accesible desde: http://localhost:8000/admin/plazas/asignacionplaza/
    """

    list_display = [
        'posicion_ranking',
        'estudiante',
        'plaza',
        'puntaje_xgboost',
        'estado',
        'date_create',              # Fecha de asignación (ModelBase)
        'status',
    ]

    list_filter   = ['estado', 'plaza__periodo', 'status']
    search_fields = ['estudiante__cedula', 'estudiante__nombres', 'plaza__codigo']
    ordering      = ['posicion_ranking']

    # Todo es de solo lectura — no se editan asignaciones manualmente
    readonly_fields = [
        'estudiante', 'plaza', 'posicion_ranking', 'puntaje_xgboost',
        'date_create', 'user_create', 'ip_create',
        'date_modification', 'user_modification', 'ip_modification',
        'date_delete', 'user_delete', 'ip_delete',
    ]

    fieldsets = (
        ('Datos de la Asignación', {
            'fields': ('estudiante', 'plaza', 'posicion_ranking', 'puntaje_xgboost', 'estado', 'observaciones')
        }),
        ('Auditoría (ModelBase)', {
            'classes': ('collapse',),
            'fields': (
                'status',
                'date_create', 'user_create', 'ip_create',
                'date_modification', 'user_modification', 'ip_modification',
                'date_delete', 'user_delete', 'ip_delete',
            )
        }),
    )
