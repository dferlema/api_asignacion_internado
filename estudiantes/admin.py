# ============================================================
# ADMIN.PY — App Estudiantes
# managed=False: muestra datos de tablas Innotech.
# Solo campos reales de estudiantil.estudiante.
# ============================================================

from django.contrib import admin
from .models import Estudiante, SituacionEconomica, CargaFamiliar


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display  = ['codigo_estudiante', 'nombre_completo', 'cedula', 'nivel_actual', 'estado']
    list_filter   = ['estado', 'modalidad']
    search_fields = ['codigo_estudiante']
    ordering      = ['codigo_estudiante']
    readonly_fields = ['id', 'id_persona', 'id_carrera', 'codigo_estudiante', 'fecha_ingreso']

    def nombre_completo(self, obj):
        return obj.nombre_completo
    nombre_completo.short_description = 'Nombre'

    def cedula(self, obj):
        return obj.cedula
    cedula.short_description = 'Cédula'


@admin.register(SituacionEconomica)
class SituacionEconomicaAdmin(admin.ModelAdmin):
    list_display  = ['id_estudiante', 'nivel_pobreza', 'ingreso_familiar', 'tiene_bono_desarrollo']
    list_filter   = ['nivel_pobreza', 'tiene_bono_desarrollo', 'trabaja']
    readonly_fields = ['id', 'id_estudiante', 'id_periodo']


@admin.register(CargaFamiliar)
class CargaFamiliarAdmin(admin.ModelAdmin):
    list_display  = ['id_estudiante', 'parentesco', 'edad', 'es_dependiente']
    list_filter   = ['parentesco', 'es_dependiente']
    readonly_fields = ['id', 'id_estudiante']