# ============================================================
# BUSINESS.PY — App Plazas (Capa 4: Lógica de Negocio)
# Consultas, creación y actualización de plazas.
# Toda escritura usa @transaction.atomic.
# ============================================================

from django.db import transaction
from .models import PlazaInternado, AsignacionPlaza


class PlazasBusiness:
    """Lógica de negocio para la gestión de plazas de internado."""

    @staticmethod
    def listar_todas():
        """Retorna todas las plazas activas (status=True via ModelBase)."""
        return PlazaInternado.objects.all()

    @staticmethod
    def listar_disponibles(periodo: str = None):
        """
        Retorna plazas con estado 'disponible'.

        Args:
            periodo (str, optional): Filtra por período si se indica.
        """
        qs = PlazaInternado.objects.filter(estado='disponible')
        if periodo:
            qs = qs.filter(periodo=periodo)
        return qs

    @staticmethod
    def obtener_por_id(plaza_id: int):
        """Obtiene una plaza activa por su ID."""
        return PlazaInternado.objects.filter(pk=plaza_id).first()

    @staticmethod
    @transaction.atomic
    def crear(datos_validados: dict) -> PlazaInternado:
        """
        Crea una nueva plaza de internado.
        ModelBase.save() registra auditoría automáticamente.

        Args:
            datos_validados (dict): Datos limpios del PlazaInternadoForm.

        Returns:
            PlazaInternado: Objeto recién creado.
        """
        plaza = PlazaInternado(**datos_validados)
        plaza.save()
        return plaza

    @staticmethod
    @transaction.atomic
    def actualizar(plaza: PlazaInternado, datos_validados: dict) -> PlazaInternado:
        """
        Actualiza los campos de una plaza existente.

        Args:
            plaza (PlazaInternado): Objeto a actualizar.
            datos_validados (dict): Campos nuevos del form.

        Returns:
            PlazaInternado: Objeto actualizado.
        """
        for campo, valor in datos_validados.items():
            setattr(plaza, campo, valor)
        plaza.save()   # ModelBase.save() registra user_modification
        return plaza

    @staticmethod
    @transaction.atomic
    def actualizar_estado(plaza: PlazaInternado, nuevo_estado: str) -> PlazaInternado:
        """
        Actualiza únicamente el estado de una plaza.

        Args:
            plaza (PlazaInternado): Objeto a actualizar.
            nuevo_estado (str):     Nuevo estado ('disponible', 'ocupada', etc.)

        Returns:
            PlazaInternado: Objeto con estado actualizado.
        """
        plaza.estado = nuevo_estado
        plaza.save()
        return plaza

    @staticmethod
    @transaction.atomic
    def eliminar(plaza: PlazaInternado):
        """
        Soft Delete de la plaza.
        ModelBase.delete() marca status=False y registra auditoría.
        """
        plaza.delete()

    @staticmethod
    def listar_asignaciones(periodo: str = None):
        """
        Retorna todas las asignaciones activas.

        Args:
            periodo (str, optional): Filtra por período del campo plaza.
        """
        qs = AsignacionPlaza.objects.select_related(
            'estudiante', 'plaza'
        ).all()
        if periodo:
            qs = qs.filter(plaza__periodo=periodo)
        return qs
