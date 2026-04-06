# ============================================================
# SERIALIZERS.PY — App Estudiantes (Capa 5: Serialización)
# managed=False: todos los campos vienen de tablas Innotech.
# No hay campos standalone ni de ModelBase.
# ============================================================

from rest_framework import serializers
from .models import Estudiante, SituacionEconomica, CargaFamiliar


class EstudianteSerializer(serializers.ModelSerializer):
    """
    Serializer completo de estudiantil.estudiante.
    Las propiedades del modelo resuelven datos desde
    core.persona, core.parroquia, estudiantil.situacion_economica
    y estudiantil.carga_familiar automáticamente.
    """
    nombre_completo                = serializers.ReadOnlyField()
    cedula                         = serializers.ReadOnlyField()
    correo                         = serializers.ReadOnlyField()
    ubicacion_tipo                 = serializers.ReadOnlyField()
    nivel_situacion_economica      = serializers.ReadOnlyField()
    total_cargas_familiares        = serializers.ReadOnlyField()
    modulos_ingles_aprobados       = serializers.ReadOnlyField()
    calificaciones_cerradas        = serializers.ReadOnlyField()
    cumple_requisitos_habilitantes = serializers.ReadOnlyField()
    promedio_academico             = serializers.ReadOnlyField()

    class Meta:
        model  = Estudiante
        fields = [
            'id',
            'codigo_estudiante',
            'nombre_completo',
            'cedula',
            'correo',
            'nivel_actual',
            'estado',
            'ubicacion_tipo',
            'nivel_situacion_economica',
            'total_cargas_familiares',
            'promedio_academico',
            'modulos_ingles_aprobados',
            'calificaciones_cerradas',
            'cumple_requisitos_habilitantes',
        ]
        read_only_fields = ['id']


class EstudianteResumenSerializer(serializers.ModelSerializer):
    """Serializer reducido para listados y ranking."""
    nombre_completo                = serializers.ReadOnlyField()
    cedula                         = serializers.ReadOnlyField()
    cumple_requisitos_habilitantes = serializers.ReadOnlyField()
    nivel_situacion_economica      = serializers.ReadOnlyField()
    total_cargas_familiares        = serializers.ReadOnlyField()
    promedio_academico             = serializers.ReadOnlyField()

    class Meta:
        model  = Estudiante
        fields = [
            'id',
            'codigo_estudiante',
            'nombre_completo',
            'cedula',
            'promedio_academico',
            'total_cargas_familiares',
            'nivel_situacion_economica',
            'cumple_requisitos_habilitantes',
        ]


class SituacionEconomicaSerializer(serializers.ModelSerializer):
    """Serializer para estudiantil.situacion_economica."""
    nivel_numerico = serializers.ReadOnlyField()

    class Meta:
        model  = SituacionEconomica
        fields = [
            'id',
            'id_estudiante',
            'id_periodo',
            'nivel_pobreza',
            'nivel_numerico',
            'ingreso_familiar',
            'numero_miembros_hogar',
            'tiene_bono_desarrollo',
            'tiene_discapacidad',
            'porcentaje_discapacidad',
            'trabaja',
            'horas_trabajo_semana',
        ]
        read_only_fields = ['id']


class CargaFamiliarSerializer(serializers.ModelSerializer):
    """Serializer para estudiantil.carga_familiar."""

    class Meta:
        model  = CargaFamiliar
        fields = ['id', 'id_estudiante', 'parentesco', 'edad', 'es_dependiente']
        read_only_fields = ['id']


class ValidacionRequisitosSerializer(serializers.Serializer):
    """Serializer para la respuesta de validación de requisitos habilitantes."""
    estudiante_id               = serializers.CharField()
    nombre_completo             = serializers.CharField()
    cedula                      = serializers.CharField()
    modulos_ingles_aprobados    = serializers.BooleanField()
    calificaciones_cerradas     = serializers.BooleanField()
    cumple_todos_los_requisitos = serializers.BooleanField()
    requisitos_faltantes        = serializers.ListField()
    mensaje                     = serializers.CharField()