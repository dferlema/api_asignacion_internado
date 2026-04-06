# ============================================================
# SERIALIZERS.PY — App Plazas (Capa 5: Serialización)
# Actualizado para modelos compatibles con Innotech BD.
# ============================================================

from rest_framework import serializers
from .models import (
    InstitucionReceptora,
    PlazaPractica,
    VerificacionRequisito,
    RankingInternado,
    AsignacionInternado,
    ApelacionInternado,
)


class InstitucionReceptoraSerializer(serializers.ModelSerializer):
    class Meta:
        model  = InstitucionReceptora
        fields = ['id', 'nombre', 'tipo', 'ciudad', 'contacto_email', 'activa']


class PlazaPracticaSerializer(serializers.ModelSerializer):
    institucion_nombre = serializers.CharField(source='institucion.nombre', read_only=True)
    periodo_display    = serializers.ReadOnlyField()
    hay_cupo           = serializers.ReadOnlyField()

    class Meta:
        model  = PlazaPractica
        fields = [
            'id', 'nombre_plaza', 'institucion', 'institucion_nombre',
            'area', 'modalidad', 'periodo_codigo', 'periodo_display',
            'cupo_total', 'cupo_disponible', 'hay_cupo',
            'fecha_inicio', 'fecha_fin', 'activa',
            'status', 'date_create',
        ]
        read_only_fields = ['id', 'status', 'date_create']


class VerificacionRequisitoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VerificacionRequisito
        fields = [
            'id', 'estudiante', 'tipo_requisito', 'nombre_requisito',
            'cumple', 'evidencia_url', 'verificado_en',
        ]
        read_only_fields = ['id', 'verificado_en']


class RankingInternadoSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.CharField(source='estudiante.nombre_completo', read_only=True)
    estudiante_cedula = serializers.CharField(source='estudiante.cedula', read_only=True)

    class Meta:
        model  = RankingInternado
        fields = [
            'id', 'posicion', 'estudiante', 'estudiante_nombre',
            'estudiante_cedula', 'puntaje_total', 'detalle_puntaje',
            'habilitado', 'periodo_codigo', 'generado_en',
        ]
        read_only_fields = ['id', 'generado_en']


class AsignacionInternadoSerializer(serializers.ModelSerializer):
    plaza_nombre       = serializers.CharField(source='plaza.nombre_plaza', read_only=True)
    institucion_nombre = serializers.CharField(source='plaza.institucion.nombre', read_only=True)

    class Meta:
        model  = AsignacionInternado
        fields = [
            'id', 'ranking', 'plaza', 'plaza_nombre',
            'institucion_nombre', 'estado', 'es_automatica',
            'fecha_asignacion',
        ]
        read_only_fields = ['id', 'fecha_asignacion']


class ApelacionInternadoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ApelacionInternado
        fields = [
            'id', 'estudiante', 'periodo', 'motivo',
            'documentos_url', 'estado', 'resolucion', 'date_create',
        ]
        read_only_fields = ['id', 'date_create']