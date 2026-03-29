# ============================================================
# MODELS.PY — App Plazas (Capa: Modelos ORM)
# Hereda de ModelBase para soft delete y auditoría automática.
# ============================================================

from django.db import models
from helpers.my_model import ModelBase
from estudiantes.models import Estudiante


class PlazaInternado(ModelBase):
    """
    Plaza disponible en una institución de salud para el internado.
    Hereda soft delete y auditoría completa de ModelBase.
    """

    ESTADO_OPCIONES = [
        ('disponible', 'Disponible'),
        ('ocupada',    'Ocupada'),
        ('reservada',  'Reservada'),
        ('cancelada',  'Cancelada'),
    ]

    AREA_OPCIONES = [
        ('clinica',          'Clínica'),
        ('cirugia',          'Cirugía'),
        ('pediatria',        'Pediatría'),
        ('ginecologia',      'Ginecología'),
        ('emergencias',      'Emergencias'),
        ('medicina_interna', 'Medicina Interna'),
        ('otro',             'Otro'),
    ]

    codigo      = models.CharField(max_length=20, unique=True, verbose_name='Código de Plaza')
    institucion = models.CharField(max_length=200, verbose_name='Institución de Salud')
    area        = models.CharField(max_length=30, choices=AREA_OPCIONES, verbose_name='Área')
    ciudad      = models.CharField(max_length=100, verbose_name='Ciudad')
    direccion   = models.TextField(blank=True, null=True, verbose_name='Dirección')
    estado      = models.CharField(max_length=15, choices=ESTADO_OPCIONES, default='disponible')
    periodo     = models.CharField(max_length=20, verbose_name='Período Académico')

    class Meta:
        verbose_name        = 'Plaza de Internado'
        verbose_name_plural = 'Plazas de Internado'
        ordering            = ['institucion', 'area']

    def __str__(self):
        return f"{self.codigo} — {self.institucion} ({self.area})"


class AsignacionPlaza(ModelBase):
    """
    Registro de la asignación de una plaza a un estudiante.
    Guarda el puntaje XGBoost para auditorías y apelaciones.
    Hereda soft delete y auditoría completa de ModelBase.
    """

    ESTADO_ASIGNACION_OPCIONES = [
        ('asignada',  'Asignada'),
        ('aceptada',  'Aceptada por el Estudiante'),
        ('rechazada', 'Rechazada por el Estudiante'),
        ('cancelada', 'Cancelada por Institución'),
    ]

    estudiante       = models.ForeignKey(
        Estudiante, on_delete=models.PROTECT, related_name='asignaciones'
    )
    plaza            = models.ForeignKey(
        PlazaInternado, on_delete=models.PROTECT, related_name='asignaciones'
    )
    posicion_ranking = models.PositiveIntegerField(verbose_name='Posición en el Ranking')
    puntaje_xgboost  = models.DecimalField(
        max_digits=6, decimal_places=4, verbose_name='Puntaje XGBoost'
    )
    estado           = models.CharField(
        max_length=15, choices=ESTADO_ASIGNACION_OPCIONES, default='asignada'
    )
    observaciones    = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name        = 'Asignación de Plaza'
        verbose_name_plural = 'Asignaciones de Plaza'
        ordering            = ['posicion_ranking']
        unique_together     = [['estudiante', 'plaza']]

    def __str__(self):
        return f"#{self.posicion_ranking} — {self.estudiante.nombre_completo} → {self.plaza.codigo}"
