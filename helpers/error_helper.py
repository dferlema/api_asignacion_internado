# ============================================================
# ERROR_HELPER.PY — Mensajes amigables para errores de BD
# Convierte errores técnicos de PostgreSQL y Django en mensajes
# comprensibles para el usuario final.
# ============================================================

from django.db import IntegrityError, DatabaseError, OperationalError


def mensaje_error_bd(excepcion: Exception) -> str:
    """
    Convierte una excepción de base de datos en un mensaje
    amigable en español para el usuario final.

    Args:
        excepcion: Excepción capturada del bloque try/except.

    Returns:
        str: Mensaje descriptivo y amigable del error.

    Ejemplo de uso en un controller:
        try:
            estudiante.save()
        except Exception as e:
            return respuesta_error_general(mensaje_error_bd(e))
    """
    mensaje = str(excepcion).lower()

    # --- Errores de unicidad (unique constraint) ---
    if 'unique' in mensaje or 'duplicate' in mensaje:
        if 'cedula' in mensaje:
            return 'Ya existe un estudiante registrado con esa cédula.'
        if 'correo' in mensaje or 'email' in mensaje:
            return 'Ya existe un registro con ese correo electrónico.'
        if 'codigo' in mensaje:
            return 'Ya existe una plaza con ese código.'
        return 'Ya existe un registro con esos datos. Verifique los campos únicos.'

    # --- Errores de referencia (foreign key) ---
    if 'foreign key' in mensaje or 'violates foreign key' in mensaje:
        return 'No se puede eliminar porque otros registros dependen de este elemento.'

    # --- Errores de nulos (not null) ---
    if 'not null' in mensaje or 'null value' in mensaje:
        return 'Faltan campos obligatorios. Verifique que todos los datos requeridos estén completos.'

    # --- Errores de longitud de campo ---
    if 'value too long' in mensaje or 'character varying' in mensaje:
        return 'Uno de los campos excede el límite máximo de caracteres permitidos.'

    # --- Error de conexión con la base de datos ---
    if isinstance(excepcion, OperationalError):
        return 'No se pudo conectar a la base de datos. Intente nuevamente en unos momentos.'

    # --- Error genérico de base de datos ---
    if isinstance(excepcion, (IntegrityError, DatabaseError)):
        return 'Ocurrió un error al procesar los datos. Por favor intente nuevamente.'

    # --- Error desconocido ---
    return 'Ocurrió un error inesperado. Contacte al administrador del sistema.'


def manejar_excepcion(excepcion: Exception, contexto: str = '') -> str:
    """
    Función de utilidad para registrar y convertir cualquier
    excepción en un mensaje amigable.

    Args:
        excepcion (Exception): La excepción capturada.
        contexto (str):        Contexto adicional para el log (opcional).

    Returns:
        str: Mensaje amigable para el usuario.

    Ejemplo:
        except Exception as e:
            mensaje = manejar_excepcion(e, contexto='generar_ranking')
            return respuesta_error_general(mensaje)
    """
    import logging
    logger = logging.getLogger(__name__)

    # Registrar el error técnico en el log del servidor
    if contexto:
        logger.error(f'[{contexto}] Error: {str(excepcion)}', exc_info=True)
    else:
        logger.error(f'Error: {str(excepcion)}', exc_info=True)

    # Retornar mensaje amigable
    return mensaje_error_bd(excepcion)
