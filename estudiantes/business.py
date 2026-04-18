# ============================================================
# BUSINESS.PY — App Estudiantes (Capa 4: Lógica de Negocio)
# managed=False: lee y escribe en tablas Innotech directamente.
# No usa ModelBase. No hay soft delete propio —
# Innotech maneja el campo 'estado' del estudiante.
#
# CORRECCIÓN: listar_habilitados() usa SQL nativo con JOIN
# a practicas.requisito_habilitante en lugar de filtrar por
# tipo_requisito (campo que NO existe en la BD real).
# ============================================================

from django.db import transaction, connection
from .models import Estudiante


def _obtener_uuids_habilitados() -> list:
    """
    Retorna lista de UUIDs de estudiantes ACTIVOS que cumplen
    AMBOS requisitos habilitantes (INGLES y CALIFICACIONES)
    consultando directamente practicas.verificacion_requisito
    con JOIN a practicas.requisito_habilitante.

    No usa tipo_requisito — ese campo no existe en la BD real.
    Filtra por rh.tipo que sí es un campo real de Innotech.

    Returns:
        list: Lista de strings UUID de estudiantes habilitados.
    """
    sql = """
        SELECT DISTINCT e.id::text
        FROM estudiantil.estudiante e
        -- Requisito inglés
        JOIN practicas.verificacion_requisito vi
          ON vi.id_estudiante = e.id AND vi.cumple = TRUE
        JOIN practicas.requisito_habilitante ri
          ON ri.id = vi.id_requisito AND ri.tipo = 'INGLES' AND ri.activo = TRUE
        -- Requisito calificaciones
        JOIN practicas.verificacion_requisito vc
          ON vc.id_estudiante = e.id AND vc.cumple = TRUE
        JOIN practicas.requisito_habilitante rc
          ON rc.id = vc.id_requisito AND rc.tipo = 'CALIFICACIONES' AND rc.activo = TRUE
        WHERE e.estado = 'ACTIVO'
    """
    with connection.cursor() as cursor:
        cursor.execute(sql)
        filas = cursor.fetchall()
    return [fila[0] for fila in filas]


class EstudiantesBusiness:

    @staticmethod
    def listar_todos():
        """
        Retorna todos los estudiantes ACTIVOS de estudiantil.estudiante
        con sus relaciones a core.persona y core.parroquia cargadas.
        """
        return Estudiante.objects.filter(
            estado='ACTIVO'
        ).select_related(
            'id_persona__id_parroquia',
            'id_carrera',
        )

    @staticmethod
    def listar_habilitados():
        """
        Retorna estudiantes ACTIVOS que tienen ambos requisitos
        habilitantes aprobados en practicas.verificacion_requisito.

        Usa SQL nativo (_obtener_uuids_habilitados) porque la tabla
        practicas.verificacion_requisito no tiene el campo tipo_requisito
        — solo tiene id_requisito (FK entero a requisito_habilitante).
        """
        uuids = _obtener_uuids_habilitados()
        if not uuids:
            return Estudiante.objects.none()
        return Estudiante.objects.filter(
            id__in=uuids,
            estado='ACTIVO',
        ).select_related(
            'id_persona__id_parroquia',
            'id_carrera',
        )

    @staticmethod
    def obtener_por_id(estudiante_id):
        """
        Obtiene un estudiante ACTIVO por su UUID.
        Carga relaciones necesarias para las propiedades del modelo.
        """
        return Estudiante.objects.filter(
            pk=estudiante_id,
            estado='ACTIVO'
        ).select_related(
            'id_persona__id_parroquia',
            'id_carrera',
        ).first()

    @staticmethod
    @transaction.atomic
    def actualizar_estado(estudiante: Estudiante, nuevo_estado: str) -> Estudiante:
        """
        Actualiza el estado del estudiante en estudiantil.estudiante.
        Es la única actualización permitida desde este sistema —
        los datos personales se gestionan desde core.persona.
        """
        estudiante.estado = nuevo_estado
        estudiante.save(update_fields=['estado'])
        return estudiante

    @staticmethod
    def validar_requisitos(estudiante: Estudiante) -> dict:
        """
        Valida los requisitos habilitantes consultando
        practicas.verificacion_requisito vía SQL nativo.
        Retorna detalle completo para la respuesta del API.
        """
        ingles         = estudiante.modulos_ingles_aprobados
        calificaciones = estudiante.calificaciones_cerradas

        faltantes = []
        if not ingles:
            faltantes.append('Módulos de inglés aprobados')
        if not calificaciones:
            faltantes.append('Calificaciones del período cerradas')

        cumple = len(faltantes) == 0

        if cumple:
            mensaje = (
                f'{estudiante.nombre_completo} cumple TODOS los requisitos '
                f'y está habilitado/a para el proceso de internado.'
            )
        else:
            mensaje = (
                f'{estudiante.nombre_completo} NO está habilitado/a. '
                f'Requisitos pendientes: {", ".join(faltantes)}.'
            )

        return {
            'estudiante_id':               str(estudiante.id),
            'nombre_completo':             estudiante.nombre_completo,
            'cedula':                      estudiante.cedula,
            'modulos_ingles_aprobados':    ingles,
            'calificaciones_cerradas':     calificaciones,
            'cumple_todos_los_requisitos': cumple,
            'requisitos_faltantes':        faltantes,
            'mensaje':                     mensaje,
        }