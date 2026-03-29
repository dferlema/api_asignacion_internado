# ============================================================
# SERIALIZERS.PY — App Plazas (Capa 5: Serialización)
# Transforma modelos PlazaInternado y AsignacionPlaza a JSON.
# ============================================================

from rest_framework import serializers
from .models import PlazaInternado, AsignacionPlaza
from estudiantes.serializers import EstudianteResumenSerializer


class PlazaInternadoSerializer(serializers.ModelSerializer):
    """Serializer completo para plazas de internado."""

    class Meta:
        model  = PlazaInternado
        fields = [
            'id', 'codigo', 'institucion', 'area',
            'ciudad', 'direccion', 'estado', 'periodo',
            # Campos de auditoría de ModelBase (solo lectura)
            'status', 'date_create', 'date_modification',
        ]
        read_only_fields = ['id', 'status', 'date_create', 'date_modification']


class AsignacionPlazaSerializer(serializers.ModelSerializer):
    """
    Serializer para asignaciones de plaza.
    Incluye datos anidados del estudiante y la plaza
    para devolver toda la información en una sola respuesta.
    """

    # Datos anidados de solo lectura (para respuestas GET)
    estudiante_detalle = EstudianteResumenSerializer(
        source='estudiante', read_only=True
    )
    plaza_detalle = PlazaInternadoSerializer(
        source='plaza', read_only=True
    )

    class Meta:
        model  = AsignacionPlaza
        fields = [
            'id',
            'estudiante',         # ID para escritura
            'estudiante_detalle', # Objeto completo para lectura
            'plaza',              # ID para escritura
            'plaza_detalle',      # Objeto completo para lectura
            'posicion_ranking',
            'puntaje_xgboost',
            'estado',
            'observaciones',
            # Auditoría de ModelBase
            'status', 'date_create',
        ]
        read_only_fields = ['id', 'status', 'date_create']
