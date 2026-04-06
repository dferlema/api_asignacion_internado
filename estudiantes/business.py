# ============================================================
# BUSINESS.PY — App Estudiantes (Capa 4: Lógica de Negocio)
# managed=False: lee y escribe en tablas Innotech directamente.
# No usa ModelBase. No hay soft delete propio —
# Innotech maneja el campo 'estado' del estudiante.
# ============================================================

from django.db import transaction, connection
from .models import Estudiante


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
        """
        con_ingles = Estudiante.objects.filter(
            verificaciones_requisitos__tipo_requisito='INGLES',
            verificaciones_requisitos__cumple=True
        ).values('id')

        con_calificaciones = Estudiante.objects.filter(
            verificaciones_requisitos__tipo_requisito='CALIFICACIONES',
            verificaciones_requisitos__cumple=True
        ).values('id')

        return Estudiante.objects.filter(
            estado='ACTIVO',
            id__in=con_ingles,
        ).filter(
            id__in=con_calificaciones
        ).select_related('id_persona__id_parroquia', 'id_carrera')

    @staticmethod
    def obtener_por_id(estudiante_id):
        """
        Obtiene un estudiante por su UUID desde estudiantil.estudiante.
        Carga relaciones necesarias para las propiedades del modelo.
        """
        return Estudiante.objects.filter(
            pk=estudiante_id,
            estado='ACTIVO'
        ).select_related(
            'id_persona__id_parroquia',
            'id_carrera'
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
        practicas.verificacion_requisito.
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