# ============================================================
# CONTROLLERS.PY — App Plazas (Capa 3: Orquestación)
# Llama a Business, serializa datos y retorna respuesta estándar.
# ============================================================

from rest_framework import status
from helpers.response_helper import (
    respuesta_exito,
    respuesta_error_general,
    respuesta_no_encontrado,
)
from helpers.error_helper import manejar_excepcion
from .business import PlazasBusiness
from .serializers import PlazaInternadoSerializer, AsignacionPlazaSerializer


class PlazasController:

    @staticmethod
    def listar():
        """Lista todas las plazas activas."""
        try:
            plazas     = PlazasBusiness.listar_todas()
            serializer = PlazaInternadoSerializer(plazas, many=True)
            return respuesta_exito(
                mensaje=f'Se encontraron {plazas.count()} plazas.',
                datos=serializer.data
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'listar_plazas'))

    @staticmethod
    def crear(datos_form: dict):
        """Crea una nueva plaza."""
        try:
            plaza      = PlazasBusiness.crear(datos_form)
            serializer = PlazaInternadoSerializer(plaza)
            return respuesta_exito(
                mensaje='Plaza creada correctamente.',
                datos=serializer.data,
                codigo=status.HTTP_201_CREATED
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'crear_plaza'))

    @staticmethod
    def detalle(plaza_id: int):
        """Retorna el detalle de una plaza por ID."""
        plaza = PlazasBusiness.obtener_por_id(plaza_id)
        if not plaza:
            return respuesta_no_encontrado(f'No se encontró la plaza con ID {plaza_id}.')
        serializer = PlazaInternadoSerializer(plaza)
        return respuesta_exito(mensaje='Plaza encontrada.', datos=serializer.data)

    @staticmethod
    def actualizar(plaza_id: int, datos_form: dict):
        """Actualiza los datos de una plaza."""
        plaza = PlazasBusiness.obtener_por_id(plaza_id)
        if not plaza:
            return respuesta_no_encontrado(f'No se encontró la plaza con ID {plaza_id}.')
        try:
            plaza_actualizada = PlazasBusiness.actualizar(plaza, datos_form)
            serializer        = PlazaInternadoSerializer(plaza_actualizada)
            return respuesta_exito(
                mensaje='Plaza actualizada correctamente.',
                datos=serializer.data
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'actualizar_plaza'))

    @staticmethod
    def eliminar(plaza_id: int):
        """Soft delete de una plaza."""
        plaza = PlazasBusiness.obtener_por_id(plaza_id)
        if not plaza:
            return respuesta_no_encontrado(f'No se encontró la plaza con ID {plaza_id}.')
        try:
            PlazasBusiness.eliminar(plaza)
            return respuesta_exito(mensaje='Plaza eliminada correctamente.')
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'eliminar_plaza'))

    @staticmethod
    def disponibles(periodo: str = None):
        """Lista solo las plazas con estado 'disponible'."""
        try:
            plazas     = PlazasBusiness.listar_disponibles(periodo)
            serializer = PlazaInternadoSerializer(plazas, many=True)
            return respuesta_exito(
                mensaje=f'{plazas.count()} plazas disponibles.',
                datos={
                    'total_disponibles': plazas.count(),
                    'plazas':            serializer.data,
                }
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'disponibles'))

    @staticmethod
    def listar_asignaciones(periodo: str = None):
        """Lista todas las asignaciones, opcionalmente filtradas por período."""
        try:
            asignaciones = PlazasBusiness.listar_asignaciones(periodo)
            serializer   = AsignacionPlazaSerializer(asignaciones, many=True)
            return respuesta_exito(
                mensaje=f'Se encontraron {asignaciones.count()} asignaciones.',
                datos=serializer.data
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'listar_asignaciones'))
