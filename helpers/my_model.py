# ============================================================
# MY_MODEL.PY — ModelBase con Soft Delete y Auditoría
# Todos los modelos del sistema deben heredar de esta clase.
# Proporciona: estado, auditoría completa e IP automáticos.
# ============================================================

from django.db import models
from django.contrib.auth.models import User


# ============================================================
# MANAGER PERSONALIZADO
# Controla qué registros devuelven las consultas por defecto
# ============================================================

class ModeloBaseManager(models.Manager):
    """
    Manager por defecto: retorna SOLO los registros activos
    (status=True). Se usa como 'objects' en todos los modelos.
    """
    def get_queryset(self):
        return super().get_queryset().filter(status=True)


class TodosLosRegistrosManager(models.Manager):
    """
    Manager secundario: retorna TODOS los registros incluyendo
    los eliminados (status=False). Se usa como 'all_objects'.
    """
    def get_queryset(self):
        return super().get_queryset()


class EliminadosManager(models.Manager):
    """
    Manager para ver solo registros eliminados (status=False).
    Útil para auditorías y recuperación de datos.
    """
    def get_queryset(self):
        return super().get_queryset().filter(status=False)


# ============================================================
# MODELO BASE ABSTRACTO
# ============================================================

class ModelBase(models.Model):
    """
    Clase base abstracta para todos los modelos del sistema.

    CAMPOS QUE PROVEE AUTOMÁTICAMENTE:
    - status:               Bandera de activo/inactivo (soft delete)
    - user_create:          Usuario que creó el registro
    - date_create:          Fecha/hora de creación
    - ip_create:            IP desde donde se creó
    - user_modification:    Usuario que hizo la última modificación
    - date_modification:    Fecha/hora de la última modificación
    - ip_modification:      IP desde donde se modificó
    - user_delete:          Usuario que eliminó el registro
    - date_delete:          Fecha/hora de eliminación (soft delete)
    - ip_delete:            IP desde donde se eliminó

    USO:
        class MiModelo(ModelBase):
            nombre = models.CharField(max_length=100)

    MANAGERS DISPONIBLES:
        MiModelo.objects          → Solo activos (default)
        MiModelo.all_objects      → Todos los registros
        MiModelo.deleted_objects  → Solo eliminados
    """

    # --- Estado del registro (Soft Delete) ---
    status = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='False = registro eliminado (soft delete). Nunca eliminar físicamente.'
    )

    # --- Auditoría: Creación ---
    user_create = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='%(class)s_creados',
        verbose_name='Creado por',
        help_text='Se asigna automáticamente. No modificar manualmente.'
    )
    date_create = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de creación',
        help_text='Se asigna automáticamente. No modificar manualmente.'
    )
    ip_create = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP de creación'
    )

    # --- Auditoría: Modificación ---
    user_modification = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='%(class)s_modificados',
        verbose_name='Modificado por'
    )
    date_modification = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de modificación'
    )
    ip_modification = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP de modificación'
    )

    # --- Auditoría: Eliminación (Soft Delete) ---
    user_delete = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='%(class)s_eliminados',
        verbose_name='Eliminado por'
    )
    date_delete = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de eliminación'
    )
    ip_delete = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP de eliminación'
    )

    # --- Managers ---
    objects         = ModeloBaseManager()       # Solo activos (default)
    all_objects     = TodosLosRegistrosManager()  # Todos
    deleted_objects = EliminadosManager()       # Solo eliminados

    class Meta:
        abstract = True  # No crea tabla propia, solo se hereda

    def save(self, *args, **kwargs):
        """
        Sobrescribe save() para registrar auditoría automática.
        Detecta si es creación o modificación comparando pk.
        El usuario e IP se obtienen del middleware ThreadLocal.
        Los desarrolladores NUNCA deben asignar user_create
        ni date_create manualmente.
        """
        from django.utils import timezone
        from helpers.middleware import obtener_request_actual

        request = obtener_request_actual()

        if self.pk is None:
            # --- Registro NUEVO: llenar campos de creación ---
            self.date_create = timezone.now()
            if request:
                self.user_create = request.user if request.user.is_authenticated else None
                self.ip_create   = self._obtener_ip(request)
        else:
            # --- Registro EXISTENTE: llenar campos de modificación ---
            self.date_modification = timezone.now()
            if request:
                self.user_modification = request.user if request.user.is_authenticated else None
                self.ip_modification   = self._obtener_ip(request)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Sobrescribe delete() para implementar Soft Delete.
        En lugar de eliminar el registro físicamente de la BD,
        marca status=False y registra quién y cuándo lo eliminó.
        Para eliminar físicamente usar: super().delete() directamente.
        """
        from django.utils import timezone
        from helpers.middleware import obtener_request_actual

        request = obtener_request_actual()

        # Marcar como eliminado (Soft Delete)
        self.status      = False
        self.date_delete = timezone.now()
        if request:
            self.user_delete = request.user if request.user.is_authenticated else None
            self.ip_delete   = self._obtener_ip(request)

        # Guardar sin registrar como modificación (using update para evitar recursión)
        type(self).all_objects.filter(pk=self.pk).update(
            status=False,
            date_delete=self.date_delete,
            user_delete=self.user_delete,
            ip_delete=self.ip_delete,
        )

    def _obtener_ip(self, request):
        """
        Extrae la IP real del cliente desde el request.
        Considera proxies reversos (X-Forwarded-For).
        """
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
