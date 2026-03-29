# ============================================================
# CONTROLLERS.PY — App Estudiantes (Capa 3: Orquestación)
# Llama a Business, serializa los datos y maneja excepciones.
# El view NO tiene lógica: solo valida el form y llama al controller.
# ============================================================

from rest_framework import status
from helpers.response_helper import (
    respuesta_exito,
    respuesta_error_validacion,
    respuesta_error_general,
    respuesta_no_encontrado,
)
from helpers.error_helper import manejar_excepcion
from .business import EstudiantesBusiness
from .serializers import EstudianteSerializer, EstudianteResumenSerializer


class EstudiantesController:
    """
    Orquesta el flujo entre la vista y la lógica de negocio.
    Patrón del ERP:
      View → valida Form → llama Controller → llama Business → serializa → respuesta estándar
    """

    @staticmethod
    def listar(request):
        """Lista todos los estudiantes activos con respuesta estándar."""
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
    def crear(datos_form: dict):
        """Crea un nuevo estudiante y retorna respuesta estándar."""
        try:
            estudiante = EstudiantesBusiness.crear(datos_form)
            serializer = EstudianteSerializer(estudiante)
            return respuesta_exito(
                mensaje='Estudiante registrado correctamente.',
                datos=serializer.data,
                codigo=status.HTTP_201_CREATED
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'crear_estudiante'))

    @staticmethod
    def detalle(estudiante_id: int):
        """Retorna el detalle de un estudiante por ID."""
        estudiante = EstudiantesBusiness.obtener_por_id(estudiante_id)
        if not estudiante:
            return respuesta_no_encontrado(f'No se encontró el estudiante con ID {estudiante_id}.')
        serializer = EstudianteSerializer(estudiante)
        return respuesta_exito(mensaje='Estudiante encontrado.', datos=serializer.data)

    @staticmethod
    def actualizar(estudiante_id: int, datos_form: dict):
        """Actualiza los datos de un estudiante existente."""
        estudiante = EstudiantesBusiness.obtener_por_id(estudiante_id)
        if not estudiante:
            return respuesta_no_encontrado(f'No se encontró el estudiante con ID {estudiante_id}.')
        try:
            estudiante_actualizado = EstudiantesBusiness.actualizar(estudiante, datos_form)
            serializer = EstudianteSerializer(estudiante_actualizado)
            return respuesta_exito(
                mensaje='Estudiante actualizado correctamente.',
                datos=serializer.data
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'actualizar_estudiante'))

    @staticmethod
    def eliminar(estudiante_id: int):
        """Realiza el soft delete de un estudiante."""
        estudiante = EstudiantesBusiness.obtener_por_id(estudiante_id)
        if not estudiante:
            return respuesta_no_encontrado(f'No se encontró el estudiante con ID {estudiante_id}.')
        try:
            EstudiantesBusiness.eliminar(estudiante)
            return respuesta_exito(mensaje='Estudiante eliminado correctamente.', codigo=status.HTTP_200_OK)
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'eliminar_estudiante'))

    @staticmethod
    def habilitados():
        """Lista solo los estudiantes que cumplen requisitos habilitantes."""
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
    def validar_requisitos(estudiante_id: int):
        """Valida los requisitos habilitantes de un estudiante."""
        estudiante = EstudiantesBusiness.obtener_por_id(estudiante_id)
        if not estudiante:
            return respuesta_no_encontrado(f'No se encontró el estudiante con ID {estudiante_id}.')
        resultado = EstudiantesBusiness.validar_requisitos(estudiante)
        return respuesta_exito(mensaje=resultado['mensaje'], datos=resultado)
