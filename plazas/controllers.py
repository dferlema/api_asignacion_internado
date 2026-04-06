# ============================================================
# CONTROLLERS.PY — App Plazas (Capa 3: Orquestación)
# Actualizado para modelos compatibles con Innotech BD.
# ============================================================

from rest_framework import status
from helpers.response_helper import (
    respuesta_exito,
    respuesta_error_general,
    respuesta_no_encontrado,
)
from helpers.error_helper import manejar_excepcion
from .business import PlazasBusiness
from .serializers import PlazaPracticaSerializer, AsignacionInternadoSerializer


class PlazasController:

    @staticmethod
    def listar():
        try:
            plazas     = PlazasBusiness.listar_todas()
            serializer = PlazaPracticaSerializer(plazas, many=True)
            return respuesta_exito(
                mensaje=f'Se encontraron {plazas.count()} plazas.',
                datos=serializer.data
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'listar_plazas'))

    @staticmethod
    def crear(datos_form: dict):
        try:
            plaza      = PlazasBusiness.crear(datos_form)
            serializer = PlazaPracticaSerializer(plaza)
            return respuesta_exito(
                mensaje='Plaza creada correctamente.',
                datos=serializer.data,
                codigo=status.HTTP_201_CREATED
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'crear_plaza'))

    @staticmethod
    def detalle(plaza_id: int):
        plaza = PlazasBusiness.obtener_por_id(plaza_id)
        if not plaza:
            return respuesta_no_encontrado(f'No se encontró la plaza con ID {plaza_id}.')
        return respuesta_exito(
            mensaje='Plaza encontrada.',
            datos=PlazaPracticaSerializer(plaza).data
        )

    @staticmethod
    def actualizar(plaza_id: int, datos_form: dict):
        plaza = PlazasBusiness.obtener_por_id(plaza_id)
        if not plaza:
            return respuesta_no_encontrado(f'No se encontró la plaza con ID {plaza_id}.')
        try:
            actualizada = PlazasBusiness.actualizar(plaza, datos_form)
            return respuesta_exito(
                mensaje='Plaza actualizada correctamente.',
                datos=PlazaPracticaSerializer(actualizada).data
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'actualizar_plaza'))

    @staticmethod
    def eliminar(plaza_id: int):
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
        try:
            plazas     = PlazasBusiness.listar_disponibles(periodo)
            serializer = PlazaPracticaSerializer(plazas, many=True)
            return respuesta_exito(
                mensaje=f'{plazas.count()} plazas con cupo disponible.',
                datos={'total': plazas.count(), 'plazas': serializer.data}
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'disponibles'))

    @staticmethod
    def listar_asignaciones(periodo: str = None):
        try:
            asignaciones = PlazasBusiness.listar_asignaciones(periodo)
            serializer   = AsignacionInternadoSerializer(asignaciones, many=True)
            return respuesta_exito(
                mensaje=f'Se encontraron {asignaciones.count()} asignaciones.',
                datos=serializer.data
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'listar_asignaciones'))