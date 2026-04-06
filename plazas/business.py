# ============================================================
# BUSINESS.PY — App Plazas (Capa 4: Lógica de Negocio)
# Actualizado para modelos compatibles con Innotech BD.
# ============================================================

from django.db import transaction
from .models import PlazaPractica, AsignacionInternado


class PlazasBusiness:

    @staticmethod
    def listar_todas():
        return PlazaPractica.objects.filter(activa=True)

    @staticmethod
    def listar_disponibles(periodo: str = None):
        qs = PlazaPractica.objects.filter(activa=True, cupo_disponible__gt=0)
        if periodo:
            qs = qs.filter(periodo_codigo=periodo)
        return qs

    @staticmethod
    def obtener_por_id(plaza_id: int):
        return PlazaPractica.objects.filter(pk=plaza_id, status=True).first()

    @staticmethod
    @transaction.atomic
    def crear(datos_validados: dict) -> PlazaPractica:
        plaza = PlazaPractica(**datos_validados)
        plaza.save()
        return plaza

    @staticmethod
    @transaction.atomic
    def actualizar(plaza: PlazaPractica, datos_validados: dict) -> PlazaPractica:
        for campo, valor in datos_validados.items():
            setattr(plaza, campo, valor)
        plaza.save()
        return plaza

    @staticmethod
    @transaction.atomic
    def eliminar(plaza: PlazaPractica):
        plaza.delete()

    @staticmethod
    def listar_asignaciones(periodo: str = None):
        qs = AsignacionInternado.objects.select_related(
            'ranking__estudiante', 'plaza__institucion'
        ).filter(status=True)
        if periodo:
            qs = qs.filter(ranking__periodo_codigo=periodo)
        return qs