# ============================================================
# MODELS.PY — App Estudiantes
# Hereda de ModelBase para soft delete y auditoría automática
# ============================================================

from django.db import models
from helpers.my_model import ModelBase


class Estudiante(ModelBase):
    """
    Modelo del estudiante. Hereda de ModelBase lo cual provee
    automáticamente: status, auditoría completa y soft delete.
    Los desarrolladores NUNCA gestionan user_create ni date_create.
    """

    ESTADO_CIVIL_OPCIONES = [
        ('soltero',     'Soltero/a'),
        ('casado',      'Casado/a'),
        ('union_libre', 'Unión Libre'),
        ('divorciado',  'Divorciado/a'),
        ('viudo',       'Viudo/a'),
    ]

    SITUACION_ECONOMICA_OPCIONES = [
        (1, 'Baja'),
        (2, 'Media-Baja'),
        (3, 'Media'),
        (4, 'Media-Alta'),
        (5, 'Alta'),
    ]

    UBICACION_OPCIONES = [
        ('urbana',     'Urbana'),
        ('rural',      'Rural'),
        ('periurbana', 'Periurbana'),
    ]

    # --- Datos personales ---
    cedula    = models.CharField(max_length=10, unique=True, verbose_name='Cédula')
    nombres   = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    correo    = models.EmailField(unique=True, verbose_name='Correo')
    telefono  = models.CharField(max_length=15, blank=True, null=True)

    # --- Variables para el algoritmo IA ---
    estado_civil         = models.CharField(max_length=20, choices=ESTADO_CIVIL_OPCIONES)
    cargas_familiares    = models.PositiveIntegerField(default=0)
    ubicacion_geografica = models.CharField(max_length=20, choices=UBICACION_OPCIONES)
    situacion_economica  = models.IntegerField(choices=SITUACION_ECONOMICA_OPCIONES)
    calificaciones       = models.DecimalField(max_digits=4, decimal_places=2)
    nivel_academico      = models.PositiveIntegerField()

    # --- Requisitos habilitantes ---
    modulos_ingles_aprobados = models.BooleanField(default=False)
    calificaciones_cerradas  = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering            = ['-date_create']  # Campo de ModelBase

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} — {self.cedula}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def cumple_requisitos_habilitantes(self):
        """Verifica ambos requisitos habilitantes de una vez."""
        return self.modulos_ingles_aprobados and self.calificaciones_cerradas
