# ============================================================
# SERIALIZERS.PY — App Estudiantes (Capa 5: Serialización)
# Transforma modelos Django a JSON y viceversa.
# ============================================================

from rest_framework import serializers
from .models import Estudiante


class EstudianteSerializer(serializers.ModelSerializer):
    """Serializer completo para respuestas de estudiante."""
    nombre_completo                = serializers.ReadOnlyField()
    cumple_requisitos_habilitantes = serializers.ReadOnlyField()

    class Meta:
        model  = Estudiante
        fields = [
            'id', 'cedula', 'nombres', 'apellidos', 'nombre_completo',
            'correo', 'telefono', 'estado_civil', 'cargas_familiares',
            'ubicacion_geografica', 'situacion_economica', 'calificaciones',
            'nivel_academico', 'modulos_ingles_aprobados', 'calificaciones_cerradas',
            'cumple_requisitos_habilitantes',
            # Campos de auditoría de ModelBase (solo lectura)
            'status', 'date_create', 'date_modification',
        ]
        read_only_fields = ['id', 'status', 'date_create', 'date_modification']


class EstudianteResumenSerializer(serializers.ModelSerializer):
    """Serializer reducido para listados y ranking."""
    nombre_completo                = serializers.ReadOnlyField()
    cumple_requisitos_habilitantes = serializers.ReadOnlyField()

    class Meta:
        model  = Estudiante
        fields = [
            'id', 'cedula', 'nombre_completo',
            'calificaciones', 'cargas_familiares',
            'situacion_economica', 'cumple_requisitos_habilitantes',
        ]
