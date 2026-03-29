# ============================================================
# BUSINESS.PY — App Estudiantes (Capa 4: Lógica de Negocio)
# Contiene TODA la lógica de negocio: consultas, creación,
# actualizaciones y validaciones de negocio.
# Usa @transaction.atomic en operaciones de escritura.
# ============================================================

from django.db import transaction
from .models import Estudiante


class EstudiantesBusiness:
    """
    Clase que encapsula toda la lógica de negocio para estudiantes.
    El controller instancia esta clase y llama a sus métodos.
    Esta capa NO conoce el request HTTP ni los serializers.
    """

    @staticmethod
    def listar_todos():
        """
        Retorna todos los estudiantes activos.
        ModelBase.objects solo devuelve los que tienen status=True.
        """
        return Estudiante.objects.all()

    @staticmethod
    def listar_habilitados():
        """
        Retorna solo estudiantes que cumplen ambos
        requisitos habilitantes y están activos.
        """
        return Estudiante.objects.filter(
            modulos_ingles_aprobados=True,
            calificaciones_cerradas=True,
        )

    @staticmethod
    def obtener_por_id(estudiante_id: int):
        """
        Obtiene un estudiante activo por su ID.

        Args:
            estudiante_id (int): ID del estudiante.

        Returns:
            Estudiante o None si no existe/está eliminado.
        """
        return Estudiante.objects.filter(pk=estudiante_id).first()

    @staticmethod
    @transaction.atomic
    def crear(datos_validados: dict) -> Estudiante:
        """
        Crea un nuevo estudiante en la base de datos.
        @transaction.atomic garantiza que si algo falla,
        no quede ningún dato parcialmente guardado.

        Args:
            datos_validados (dict): Datos limpios del form.

        Returns:
            Estudiante: El objeto recién creado.

        Raises:
            Exception: Si falla la creación (manejo en el controller).
        """
        estudiante = Estudiante(**datos_validados)
        estudiante.save()   # ModelBase.save() registra auditoría automáticamente
        return estudiante

    @staticmethod
    @transaction.atomic
    def actualizar(estudiante: Estudiante, datos_validados: dict) -> Estudiante:
        """
        Actualiza los campos de un estudiante existente.

        Args:
            estudiante (Estudiante): Objeto a actualizar.
            datos_validados (dict):  Campos nuevos del form.

        Returns:
            Estudiante: El objeto actualizado.
        """
        for campo, valor in datos_validados.items():
            setattr(estudiante, campo, valor)
        estudiante.save()   # ModelBase.save() registra user_modification e ip
        return estudiante

    @staticmethod
    @transaction.atomic
    def eliminar(estudiante: Estudiante):
        """
        Realiza un Soft Delete del estudiante.
        ModelBase.delete() marca status=False y registra
        quién y cuándo eliminó el registro. Nunca borra físicamente.

        Args:
            estudiante (Estudiante): Objeto a eliminar lógicamente.
        """
        estudiante.delete()   # Soft Delete de ModelBase

    @staticmethod
    def validar_requisitos(estudiante: Estudiante) -> dict:
        """
        Construye la respuesta de validación de requisitos
        habilitantes con detalle de cada uno.

        Args:
            estudiante (Estudiante): Estudiante a validar.

        Returns:
            dict con el resultado de validación y mensaje descriptivo.
        """
        faltantes = []
        if not estudiante.modulos_ingles_aprobados:
            faltantes.append('Módulos de inglés aprobados')
        if not estudiante.calificaciones_cerradas:
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
            'estudiante_id':                estudiante.id,
            'nombre_completo':              estudiante.nombre_completo,
            'cedula':                       estudiante.cedula,
            'modulos_ingles_aprobados':     estudiante.modulos_ingles_aprobados,
            'calificaciones_cerradas':      estudiante.calificaciones_cerradas,
            'cumple_todos_los_requisitos':  cumple,
            'requisitos_faltantes':         faltantes,
            'mensaje':                      mensaje,
        }
