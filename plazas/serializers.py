# ============================================================
# SERIALIZERS.PY — App Plazas (Capa 5: Serialización)
# managed=False: campos reales de tablas Innotech.
# CORRECCIÓN: eliminado tipo_requisito (no existe en BD real).
# Todos los campos FK usan el nombre real del modelo (id_*).
# ============================================================

from rest_framework import serializers
from .models import (
    InstitucionReceptora,
    PlazaPractica,
    VerificacionRequisito,
    RankingInternado,
    AsignacionInternado,
    ApelacionInternado,
    ModeloIA,
)


class InstitucionReceptoraSerializer(serializers.ModelSerializer):
    class Meta:
        model  = InstitucionReceptora
        fields = ['id', 'nombre', 'id_tipo', 'contacto_email', 'activa']
        read_only_fields = ['id']


class PlazaPracticaSerializer(serializers.ModelSerializer):
    institucion_nombre = serializers.CharField(
        source='id_institucion.nombre', read_only=True
    )
    periodo_codigo = serializers.ReadOnlyField()
    hay_cupo       = serializers.ReadOnlyField()

    class Meta:
        model  = PlazaPractica
        fields = [
            'id',
            'nombre_plaza',
            'id_institucion',
            'institucion_nombre',
            'id_periodo',
            'periodo_codigo',
            'cupo_total',
            'cupo_disponible',
            'hay_cupo',
            'fecha_inicio',
            'fecha_fin',
            'activa',
        ]
        read_only_fields = ['id']


class VerificacionRequisitoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VerificacionRequisito
        fields = [
            'id',
            'id_estudiante',
            'id_requisito',
            'id_periodo',
            'cumple',
            'evidencia_url',
            'verificado_en',
        ]
        read_only_fields = ['id', 'verificado_en']


class RankingInternadoSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.CharField(
        source='id_estudiante.nombre_completo', read_only=True
    )
    estudiante_cedula = serializers.CharField(
        source='id_estudiante.cedula', read_only=True
    )
    periodo_codigo = serializers.CharField(
        source='id_periodo.codigo', read_only=True
    )

    class Meta:
        model  = RankingInternado
        fields = [
            'id',
            'posicion',
            'id_estudiante',
            'estudiante_nombre',
            'estudiante_cedula',
            'id_periodo',
            'periodo_codigo',
            'puntaje_total',
            'detalle_puntaje',
            'habilitado',
            'generado_por_ia',
            'generado_en',
        ]
        read_only_fields = ['id', 'generado_en']


class AsignacionInternadoSerializer(serializers.ModelSerializer):
    plaza_nombre       = serializers.CharField(
        source='id_plaza.nombre_plaza', read_only=True
    )
    institucion_nombre = serializers.CharField(
        source='id_plaza.id_institucion.nombre', read_only=True
    )

    class Meta:
        model  = AsignacionInternado
        fields = [
            'id',
            'id_ranking',
            'id_plaza',
            'plaza_nombre',
            'institucion_nombre',
            'estado',
            'es_automatica',
            'fecha_asignacion',
        ]
        read_only_fields = ['id', 'fecha_asignacion']


class ApelacionInternadoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ApelacionInternado
        fields = [
            'id',
            'id_estudiante',
            'id_periodo',
            'motivo',
            'documentos_url',
            'estado',
            'resolucion',
            'creado_en',
        ]
        read_only_fields = ['id', 'creado_en']