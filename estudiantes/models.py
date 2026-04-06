# ============================================================
# MODELS.PY — App Estudiantes
# managed=False en TODOS los modelos.
# Django NO crea ni migra ninguna tabla.
# Todas las tablas existen en la BD Innotech (innotech_db.sql).
#
# Mapeo exacto:
#   Parroquia          → core.parroquia
#   Periodo            → academico.periodo
#   Persona            → core.persona
#   Carrera            → academico.carrera
#   Estudiante         → estudiantil.estudiante
#   SituacionEconomica → estudiantil.situacion_economica
#   CargaFamiliar      → estudiantil.carga_familiar
# ============================================================

import uuid
from django.db import models


# ============================================================
# TABLAS DEL ESQUEMA core
# ============================================================

class Parroquia(models.Model):
    """
    core.parroquia — Ubicación geográfica del estudiante.
    tipo: 'URBANA' o 'RURAL' — variable para XGBoost.
    """
    id       = models.SmallIntegerField(primary_key=True)
    nombre   = models.CharField(max_length=80)
    tipo     = models.CharField(
        max_length=10,
        choices=[('URBANA', 'Urbana'), ('RURAL', 'Rural')],
        null=True, blank=True
    )
    latitud  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        managed  = False
        db_table = 'core\".\"parroquia'

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"


class Persona(models.Model):
    """
    core.persona — Tabla raíz de toda entidad humana del sistema.
    Contiene: nombre, cédula, correo, teléfono, parroquia.
    """
    id                    = models.UUIDField(primary_key=True, default=uuid.uuid4)
    numero_identificacion = models.CharField(max_length=20)
    primer_nombre         = models.CharField(max_length=60)
    segundo_nombre        = models.CharField(max_length=60, null=True, blank=True)
    primer_apellido       = models.CharField(max_length=60)
    segundo_apellido      = models.CharField(max_length=60, null=True, blank=True)
    email_personal        = models.EmailField(max_length=120, null=True, blank=True)
    email_institucional   = models.EmailField(max_length=120, null=True, blank=True)
    telefono_movil        = models.CharField(max_length=15, null=True, blank=True)
    id_parroquia          = models.ForeignKey(
        Parroquia,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_parroquia'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        managed  = False
        db_table = 'core\".\"persona'

    def __str__(self):
        return f"{self.primer_apellido} {self.primer_nombre} — {self.numero_identificacion}"

    @property
    def nombre_completo(self):
        partes = [self.primer_nombre]
        if self.segundo_nombre:
            partes.append(self.segundo_nombre)
        partes.append(self.primer_apellido)
        if self.segundo_apellido:
            partes.append(self.segundo_apellido)
        return ' '.join(partes)


# ============================================================
# TABLAS DEL ESQUEMA academico
# ============================================================

class Periodo(models.Model):
    """
    academico.periodo — Período académico (ej: 2024-1).
    Reemplaza el VARCHAR periodo_codigo que usábamos antes.
    """
    id           = models.SmallIntegerField(primary_key=True)
    nombre       = models.CharField(max_length=40)
    codigo       = models.CharField(max_length=10, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField()
    activo       = models.BooleanField(default=True)
    en_curso     = models.BooleanField(default=False)

    class Meta:
        managed  = False
        db_table = 'academico\".\"periodo'

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Carrera(models.Model):
    """
    academico.carrera — Carrera a la que pertenece el estudiante.
    """
    id     = models.SmallIntegerField(primary_key=True)
    nombre = models.CharField(max_length=120)
    codigo = models.CharField(max_length=20, unique=True)

    class Meta:
        managed  = False
        db_table = 'academico\".\"carrera'

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


# ============================================================
# TABLAS DEL ESQUEMA estudiantil
# ============================================================

class Estudiante(models.Model):
    """
    estudiantil.estudiante — Tabla principal del estudiante en Innotech.
    UUID como PK. Vinculado a core.persona para datos personales.

    IMPORTANTE: managed=False — Django NO crea esta tabla.
    La tabla ya existe en la BD Innotech.

    Para las variables del ranking XGBoost se usan:
    - promedio: calculado desde estudiantil.calificacion (vista v_promedio_estudiante_periodo)
    - cargas: conteo desde estudiantil.carga_familiar
    - situacion_economica: desde estudiantil.situacion_economica
    - ubicacion: desde core.parroquia via core.persona
    - nivel_actual: campo directo
    - requisitos habilitantes: desde practicas.verificacion_requisito
    """
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_persona        = models.OneToOneField(
        Persona,
        on_delete=models.PROTECT,
        db_column='id_persona',
        related_name='estudiante'
    )
    id_carrera        = models.ForeignKey(
        Carrera,
        on_delete=models.PROTECT,
        db_column='id_carrera',
        related_name='estudiantes'
    )
    codigo_estudiante = models.CharField(max_length=20, unique=True)
    fecha_ingreso     = models.DateField()
    nivel_actual      = models.SmallIntegerField(null=True, blank=True)
    modalidad         = models.CharField(
        max_length=20,
        choices=[('PRESENCIAL','Presencial'),('VIRTUAL','Virtual'),('HIBRIDA','Híbrida')],
        null=True, blank=True
    )
    estado            = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVO','Activo'), ('SUSPENDIDO','Suspendido'),
            ('RETIRADO','Retirado'), ('GRADUADO','Graduado'), ('BECA','Con Beca'),
        ],
        default='ACTIVO'
    )
    beca              = models.BooleanField(default=False)
    tipo_beca         = models.CharField(max_length=60, null=True, blank=True)

    class Meta:
        managed  = False
        db_table = 'estudiantil\".\"estudiante'

    def __str__(self):
        return f"{self.nombre_completo} — {self.cedula}"

    # ── Propiedades que resuelven datos desde tablas relacionadas ──

    @property
    def nombre_completo(self):
        return self.id_persona.nombre_completo

    @property
    def cedula(self):
        return self.id_persona.numero_identificacion

    @property
    def correo(self):
        return self.id_persona.email_institucional or self.id_persona.email_personal or ''

    @property
    def ubicacion_tipo(self):
        """Retorna URBANA o RURAL desde core.parroquia via core.persona."""
        if self.id_persona.id_parroquia:
            return self.id_persona.id_parroquia.tipo
        return None

    @property
    def nivel_situacion_economica(self):
        """
        Retorna nivel numérico 1-4 para XGBoost desde
        estudiantil.situacion_economica (último registro).
        """
        sit = self.situaciones_economicas.order_by('-id').first()
        if sit:
            return sit.nivel_numerico
        return 3  # valor por defecto: MEDIA

    @property
    def total_cargas_familiares(self):
        """Retorna conteo de dependientes desde estudiantil.carga_familiar."""
        return self.cargas_familiares.filter(es_dependiente=True).count()

    @property
    def modulos_ingles_aprobados(self):
        """
        Verifica si el estudiante aprobó inglés desde
        practicas.verificacion_requisito.
        """
        return self.verificaciones_requisitos.filter(
            tipo_requisito='INGLES',
            cumple=True
        ).exists()

    @property
    def calificaciones_cerradas(self):
        """
        Verifica si las calificaciones están cerradas desde
        practicas.verificacion_requisito.
        """
        return self.verificaciones_requisitos.filter(
            tipo_requisito='CALIFICACIONES',
            cumple=True
        ).exists()

    @property
    def cumple_requisitos_habilitantes(self):
        return self.modulos_ingles_aprobados and self.calificaciones_cerradas

    @property
    def promedio_academico(self):
        """
        Retorna promedio desde la vista estudiantil.v_promedio_estudiante_periodo.
        Si no hay calificaciones registradas retorna None.
        """
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT promedio
                FROM estudiantil.v_promedio_estudiante_periodo
                WHERE id_estudiante = %s
                ORDER BY id_periodo DESC
                LIMIT 1
                """,
                [str(self.id)]
            )
            row = cursor.fetchone()
        return float(row[0]) if row and row[0] else None


class SituacionEconomica(models.Model):
    """
    estudiantil.situacion_economica — Datos socioeconómicos del estudiante.
    Un estudiante tiene una situación por período.
    managed=False — tabla existente en Innotech.
    """
    NIVEL_POBREZA_OPCIONES = [
        ('EXTREMA', 'Pobreza Extrema'),
        ('BAJA',    'Nivel Bajo'),
        ('MEDIA',   'Nivel Medio'),
        ('ALTA',    'Nivel Alto'),
    ]

    id                      = models.AutoField(primary_key=True)
    id_estudiante           = models.ForeignKey(
        Estudiante,
        on_delete=models.PROTECT,
        db_column='id_estudiante',
        related_name='situaciones_economicas'
    )
    id_periodo              = models.ForeignKey(
        Periodo,
        on_delete=models.PROTECT,
        db_column='id_periodo',
        null=True, blank=True
    )
    ingreso_familiar        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    numero_miembros_hogar   = models.SmallIntegerField(null=True, blank=True)
    nivel_pobreza           = models.CharField(max_length=20, choices=NIVEL_POBREZA_OPCIONES, null=True, blank=True)
    tiene_bono_desarrollo   = models.BooleanField(default=False)
    tiene_discapacidad      = models.BooleanField(default=False)
    porcentaje_discapacidad = models.SmallIntegerField(null=True, blank=True)
    trabaja                 = models.BooleanField(default=False)
    horas_trabajo_semana    = models.SmallIntegerField(null=True, blank=True)
    actualizado_en          = models.DateField(auto_now=True)

    class Meta:
        managed     = False
        db_table    = 'estudiantil\".\"situacion_economica'
        unique_together = [['id_estudiante', 'id_periodo']]

    def __str__(self):
        return f"{self.id_estudiante} — {self.nivel_pobreza}"

    @property
    def nivel_numerico(self):
        """
        Convierte nivel_pobreza a escala 1-4 para XGBoost.
        EXTREMA=1 (mayor prioridad), ALTA=4 (menor prioridad).
        """
        mapa = {'EXTREMA': 1, 'BAJA': 2, 'MEDIA': 3, 'ALTA': 4}
        return mapa.get(self.nivel_pobreza, 3)


class CargaFamiliar(models.Model):
    """
    estudiantil.carga_familiar — Dependientes económicos del estudiante.
    managed=False — tabla existente en Innotech.
    """
    PARENTESCO_OPCIONES = [
        ('HIJO',     'Hijo/a'),
        ('PADRE',    'Padre'),
        ('MADRE',    'Madre'),
        ('CONYUGUE', 'Cónyuge'),
        ('HERMANO',  'Hermano/a'),
        ('OTRO',     'Otro'),
    ]

    id            = models.AutoField(primary_key=True)
    id_estudiante = models.ForeignKey(
        Estudiante,
        on_delete=models.PROTECT,
        db_column='id_estudiante',
        related_name='cargas_familiares'
    )
    parentesco    = models.CharField(max_length=30, choices=PARENTESCO_OPCIONES)
    edad          = models.SmallIntegerField(null=True, blank=True)
    es_dependiente = models.BooleanField(default=True)

    class Meta:
        managed  = False
        db_table = 'estudiantil\".\"carga_familiar'

    def __str__(self):
        return f"{self.id_estudiante} — {self.parentesco}"