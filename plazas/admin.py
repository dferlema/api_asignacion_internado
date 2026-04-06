# ============================================================
# ADMIN.PY — App Plazas
# Actualizado para modelos managed=False de Innotech BD.
# Nota: el admin de Django puede mostrar modelos managed=False
# pero NO puede crear/editar registros en tablas de solo lectura
# si la BD no permite escritura directa desde este esquema.
# ============================================================

from django.contrib import admin
from .models import (
    InstitucionReceptora,
    PlazaPractica,
    VerificacionRequisito,
    RankingInternado,
    AsignacionInternado,
    ApelacionInternado,
    ModeloIA,
    LogPrediccion,
)


@admin.register(InstitucionReceptora)
class InstitucionReceptoraAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'activa']
    search_fields = ['nombre']


@admin.register(PlazaPractica)
class PlazaPracticaAdmin(admin.ModelAdmin):
    list_display  = ['nombre_plaza', 'id_institucion', 'cupo_total', 'cupo_disponible', 'activa']
    list_filter   = ['activa']
    search_fields = ['nombre_plaza', 'id_institucion__nombre']


@admin.register(VerificacionRequisito)
class VerificacionRequisitoAdmin(admin.ModelAdmin):
    list_display  = ['id_estudiante', 'id_requisito', 'cumple', 'verificado_en']
    list_filter   = ['cumple']
    readonly_fields = ['id', 'id_estudiante', 'id_requisito', 'id_periodo', 'verificado_en']


@admin.register(RankingInternado)
class RankingInternadoAdmin(admin.ModelAdmin):
    list_display  = ['posicion', 'id_estudiante', 'puntaje_total', 'habilitado', 'id_periodo', 'generado_en']
    list_filter   = ['habilitado', 'generado_por_ia']
    ordering      = ['posicion']


@admin.register(AsignacionInternado)
class AsignacionInternadoAdmin(admin.ModelAdmin):
    list_display  = ['id_ranking', 'id_plaza', 'estado', 'es_automatica', 'fecha_asignacion']
    list_filter   = ['estado', 'es_automatica']


@admin.register(ApelacionInternado)
class ApelacionInternadoAdmin(admin.ModelAdmin):
    list_display  = ['id_estudiante', 'estado', 'creado_en']
    list_filter   = ['estado']


@admin.register(ModeloIA)
class ModeloIAAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'version', 'tipo', 'activo', 'fecha_despliegue']
    list_filter   = ['tipo', 'activo']


@admin.register(LogPrediccion)
class LogPrediccionAdmin(admin.ModelAdmin):
    list_display  = ['id', 'id_modelo', 'entidad_tipo', 'entidad_id', 'confianza', 'tiempo_ms', 'creado_en']
    list_filter   = ['id_modelo', 'entidad_tipo']
    ordering      = ['-creado_en']