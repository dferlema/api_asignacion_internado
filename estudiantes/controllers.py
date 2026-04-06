# ============================================================
# CONTROLLERS.PY — App Estudiantes (Capa 3: Orquestación)
# managed=False: pk es UUID como string.
# Lee desde estudiantil.estudiante (Innotech).
# ============================================================

from helpers.response_helper import (
    respuesta_exito,
    respuesta_error_general,
    respuesta_no_encontrado,
)
from helpers.error_helper import manejar_excepcion
from .business import EstudiantesBusiness
from .serializers import EstudianteSerializer, EstudianteResumenSerializer


class EstudiantesController:

    @staticmethod
    def listar():
        """Lista estudiantes ACTIVOS de estudiantil.estudiante."""
        try:
            estudiantes = EstudiantesBusiness.listar_todos()
            serializer  = EstudianteSerializer(estudiantes, many=True)
            return respuesta_exito(
                mensaje=f'Se encontraron {estudiantes.count()} estudiantes.',
                datos=serializer.data
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'listar_estudiantes'))

    @staticmethod
    def detalle(estudiante_id):
        """Retorna detalle de un estudiante por UUID."""
        estudiante = EstudiantesBusiness.obtener_por_id(estudiante_id)
        if not estudiante:
            return respuesta_no_encontrado(
                f'No se encontró el estudiante con ID {estudiante_id}.'
            )
        serializer = EstudianteSerializer(estudiante)
        return respuesta_exito(mensaje='Estudiante encontrado.', datos=serializer.data)

    @staticmethod
    def habilitados():
        """Lista estudiantes que cumplen requisitos habilitantes."""
        try:
            estudiantes = EstudiantesBusiness.listar_habilitados()
            serializer  = EstudianteResumenSerializer(estudiantes, many=True)
            return respuesta_exito(
                mensaje=f'{estudiantes.count()} estudiantes habilitados para internado.',
                datos={
                    'total_habilitados': estudiantes.count(),
                    'estudiantes':       serializer.data,
                }
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'habilitados'))

    @staticmethod
    def validar_requisitos(estudiante_id):
        """Valida requisitos habilitantes de un estudiante."""
        estudiante = EstudiantesBusiness.obtener_por_id(estudiante_id)
        if not estudiante:
            return respuesta_no_encontrado(
                f'No se encontró el estudiante con ID {estudiante_id}.'
            )
        resultado = EstudiantesBusiness.validar_requisitos(estudiante)
        return respuesta_exito(mensaje=resultado['mensaje'], datos=resultado)