# ============================================================
# RESPONSE_HELPER.PY — Formato de respuesta estándar del ERP
# Toda respuesta de la API debe usar este helper.
# Formato: { "success": bool, "message": str, "data": any }
# ============================================================

from rest_framework.response import Response
from rest_framework import status


def respuesta_exito(mensaje: str, datos=None, codigo: int = status.HTTP_200_OK) -> Response:
    """
    Retorna una respuesta HTTP de éxito con el formato estándar del ERP.

    Args:
        mensaje (str): Mensaje descriptivo del resultado.
        datos (any):   Datos a retornar (dict, list, None).
        codigo (int):  Código HTTP (default: 200).

    Returns:
        Response con formato:
        {
            "success": true,
            "message": "Operación completada.",
            "data": { ... }
        }

    Ejemplo:
        return respuesta_exito(
            mensaje="Estudiante registrado correctamente.",
            datos=serializer.data,
            codigo=status.HTTP_201_CREATED
        )
    """
    return Response(
        {
            'success': True,
            'message': mensaje,
            'data':    datos,
        },
        status=codigo
    )


def respuesta_error_validacion(mensaje: str, errores: dict = None) -> Response:
    """
    Retorna una respuesta HTTP 400 para errores de validación.

    Args:
        mensaje (str):   Mensaje descriptivo del error.
        errores (dict):  Diccionario con errores por campo.

    Returns:
        Response con formato:
        {
            "success": false,
            "message": "Datos inválidos.",
            "errors": { "campo": ["Error específico"] }
        }

    Ejemplo:
        return respuesta_error_validacion(
            mensaje="Los datos ingresados no son válidos.",
            errores=form.errors
        )
    """
    cuerpo = {
        'success': False,
        'message': mensaje,
    }
    if errores:
        cuerpo['errors'] = errores

    return Response(cuerpo, status=status.HTTP_400_BAD_REQUEST)


def respuesta_error_general(mensaje: str, codigo: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> Response:
    """
    Retorna una respuesta HTTP de error general (no de validación).

    Args:
        mensaje (str): Descripción del error.
        codigo (int):  Código HTTP (default: 500).

    Returns:
        Response con formato:
        {
            "success": false,
            "message": "Descripción del error."
        }

    Ejemplo:
        return respuesta_error_general(
            mensaje="No se pudo generar el ranking.",
            codigo=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    """
    return Response(
        {
            'success': False,
            'message': mensaje,
        },
        status=codigo
    )


def respuesta_no_encontrado(mensaje: str = "Recurso no encontrado.") -> Response:
    """
    Retorna una respuesta HTTP 404.

    Args:
        mensaje (str): Descripción de lo que no se encontró.

    Returns:
        Response con formato:
        {
            "success": false,
            "message": "Recurso no encontrado."
        }
    """
    return Response(
        {
            'success': False,
            'message': mensaje,
        },
        status=status.HTTP_404_NOT_FOUND
    )
