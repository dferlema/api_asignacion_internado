# ============================================================
# MODELS.PY — App Plazas
# managed=False en TODOS los modelos.
# Django NO crea ni migra ninguna tabla.
# Todas las tablas existen en la BD Innotech (innotech_db.sql).
#
# Mapeo exacto:
#   TipoInstitucionReceptora → practicas.tipo_institucion_receptora
#   InstitucionReceptora     → practicas.institucion_receptora
#   ModalidadPractica        → practicas.modalidad_practica
#   PlazaPractica            → practicas.plaza_practica
#   VerificacionRequisito    → practicas.verificacion_requisito
#   RankingInternado         → practicas.ranking_internado
#   AsignacionInternado      → practicas.asignacion_internado
#   ApelacionInternado       → practicas.apelacion_internado
#   ModeloIA                 → ia.modelo_ia
#   LogPrediccion            → ia.log_prediccion
# ============================================================

from django.db import models
from estudiantes.models import Estudiante, Periodo, Carrera, Persona


# ============================================================
# TABLAS DEL ESQUEMA practicas — Catálogos
# ============================================================

class TipoInstitucionReceptora(models.Model):
    """practicas.tipo_institucion_receptora — Catálogo de tipos de institución."""
    id     = models.SmallIntegerField(primary_key=True)
    nombre = models.CharField(max_length=60)

    class Meta:
        managed  = False
        db_table = 'practicas\".\"tipo_institucion_receptora'

    def __str__(self):
        return self.nombre


class ModalidadPractica(models.Model):
    """practicas.modalidad_practica — INTERNADO, PASANTIA, VINCULACION_COMUNITARIA."""
    id     = models.SmallIntegerField(primary_key=True)
    nombre = models.CharField(max_length=80)

    class Meta:
        managed  = False
        db_table = 'practicas\".\"modalidad_practica'

    def __str__(self):
        return self.nombre


# ============================================================
# TABLAS DEL ESQUEMA practicas — Entidades principales
# ============================================================

class InstitucionReceptora(models.Model):
    """
    practicas.institucion_receptora — Hospital, clínica u organización
    donde el estudiante realiza el internado.
    managed=False — tabla existente en Innotech.
    """
    id              = models.AutoField(primary_key=True)
    id_tipo         = models.ForeignKey(
        TipoInstitucionReceptora,
        on_delete=models.PROTECT,
        db_column='id_tipo'
    )
    nombre          = models.CharField(max_length=200)
    ruc             = models.CharField(max_length=13, null=True, blank=True)
    id_parroquia    = models.SmallIntegerField(null=True, blank=True)
    direccion       = models.CharField(max_length=200, null=True, blank=True)
    contacto_nombre = models.CharField(max_length=120, null=True, blank=True)
    contacto_email  = models.EmailField(max_length=120, null=True, blank=True)
    contacto_tel    = models.CharField(max_length=15, null=True, blank=True)
    latitud         = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud        = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    activa          = models.BooleanField(default=True)

    class Meta:
        managed  = False
        db_table = 'practicas\".\"institucion_receptora'

    def __str__(self):
        return self.nombre


class PlazaPractica(models.Model):
    """
    practicas.plaza_practica — Plaza disponible en una institución receptora.
    Incluye cupo_total y cupo_disponible con restricción CHECK.
    FK a academico.periodo en lugar de VARCHAR.
    managed=False — tabla existente en Innotech.
    """
    AREA_OPCIONES = [
        ('clinica',          'Clínica'),
        ('cirugia',          'Cirugía'),
        ('pediatria',        'Pediatría'),
        ('ginecologia',      'Ginecología'),
        ('emergencias',      'Emergencias'),
        ('medicina_interna', 'Medicina Interna'),
        ('otro',             'Otro'),
    ]

    id                     = models.AutoField(primary_key=True)
    id_institucion         = models.ForeignKey(
        InstitucionReceptora,
        on_delete=models.PROTECT,
        db_column='id_institucion',
        related_name='plazas'
    )
    id_carrera             = models.ForeignKey(
        Carrera,
        on_delete=models.PROTECT,
        db_column='id_carrera',
        null=True, blank=True
    )
    id_modalidad           = models.ForeignKey(
        ModalidadPractica,
        on_delete=models.PROTECT,
        db_column='id_modalidad',
        null=True, blank=True
    )
    id_periodo             = models.ForeignKey(
        Periodo,
        on_delete=models.PROTECT,
        db_column='id_periodo',
        null=True, blank=True,
        related_name='plazas'
    )
    nombre_plaza           = models.CharField(max_length=200)
    cupo_total             = models.SmallIntegerField(default=1)
    cupo_disponible        = models.SmallIntegerField(default=1)
    fecha_inicio           = models.DateField(null=True, blank=True)
    fecha_fin              = models.DateField(null=True, blank=True)
    descripcion            = models.TextField(null=True, blank=True)
    requisitos_especificos = models.TextField(null=True, blank=True)
    activa                 = models.BooleanField(default=True)

    class Meta:
        managed  = False
        db_table = 'practicas\".\"plaza_practica'

    def __str__(self):
        return f"{self.nombre_plaza} — {self.id_institucion.nombre}"

    @property
    def hay_cupo(self):
        return self.cupo_disponible > 0

    @property
    def periodo_codigo(self):
        """Retorna el código del período para compatibilidad con el business.py."""
        return self.id_periodo.codigo if self.id_periodo else None


class VerificacionRequisito(models.Model):
    """
    practicas.verificacion_requisito — Verificación formal de cada
    requisito habilitante del estudiante.
    managed=False — tabla existente en Innotech.
    """
    TIPO_REQUISITO_OPCIONES = [
        ('MODULO_APROBADO', 'Módulo Aprobado'),
        ('CALIFICACIONES',  'Calificaciones Cerradas'),
        ('INGLES',          'Módulos de Inglés'),
        ('OTRO',            'Otro'),
    ]

    id               = models.AutoField(primary_key=True)
    id_estudiante    = models.ForeignKey(
        Estudiante,
        on_delete=models.PROTECT,
        db_column='id_estudiante',
        related_name='verificaciones_requisitos'
    )
    # id_requisito referencia a practicas.requisito_habilitante
    # Se guarda como entero simple para no agregar complejidad
    id_requisito     = models.IntegerField()
    id_periodo       = models.ForeignKey(
        Periodo,
        on_delete=models.PROTECT,
        db_column='id_periodo',
        null=True, blank=True
    )
    cumple           = models.BooleanField()
    evidencia_url    = models.URLField(max_length=500, null=True, blank=True)
    verificado_por   = models.UUIDField(null=True, blank=True)
    verificado_en    = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed     = False
        db_table    = 'practicas\".\"verificacion_requisito'
        unique_together = [['id_estudiante', 'id_requisito', 'id_periodo']]

    def __str__(self):
        estado = 'Cumple' if self.cumple else 'No cumple'
        return f"{self.id_estudiante} — requisito {self.id_requisito} → {estado}"


class RankingInternado(models.Model):
    """
    practicas.ranking_internado — Ranking persistido generado por XGBoost.
    detalle_puntaje almacena el desglose por criterio en JSONB.
    Un estudiante tiene un ranking por período.
    managed=False — tabla existente en Innotech.
    """
    id              = models.AutoField(primary_key=True)
    id_estudiante   = models.ForeignKey(
        Estudiante,
        on_delete=models.PROTECT,
        db_column='id_estudiante',
        related_name='rankings'
    )
    id_periodo      = models.ForeignKey(
        Periodo,
        on_delete=models.PROTECT,
        db_column='id_periodo',
        null=True, blank=True,
        related_name='rankings'
    )
    id_carrera      = models.ForeignKey(
        Carrera,
        on_delete=models.PROTECT,
        db_column='id_carrera',
        null=True, blank=True
    )
    puntaje_total   = models.DecimalField(max_digits=6, decimal_places=4)
    detalle_puntaje = models.JSONField(null=True, blank=True)
    posicion        = models.IntegerField(null=True, blank=True)
    habilitado      = models.BooleanField(default=False)
    generado_por_ia = models.BooleanField(default=True)
    observaciones   = models.TextField(null=True, blank=True)
    generado_en     = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed     = False
        db_table    = 'practicas\".\"ranking_internado'
        unique_together = [['id_estudiante', 'id_periodo']]

    def __str__(self):
        return f"#{self.posicion} — {self.id_estudiante} (puntaje: {self.puntaje_total})"


class AsignacionInternado(models.Model):
    """
    practicas.asignacion_internado — Asignación oficial de una plaza.
    Siempre referencia al ranking que la justificó.
    managed=False — tabla existente en Innotech.
    """
    ESTADO_OPCIONES = [
        ('ASIGNADA',   'Asignada'),
        ('CONFIRMADA', 'Confirmada'),
        ('RECHAZADA',  'Rechazada'),
        ('REASIGNADA', 'Reasignada'),
        ('CANCELADA',  'Cancelada'),
    ]

    id               = models.AutoField(primary_key=True)
    id_ranking       = models.OneToOneField(
        RankingInternado,
        on_delete=models.PROTECT,
        db_column='id_ranking',
        related_name='asignacion'
    )
    id_plaza         = models.ForeignKey(
        PlazaPractica,
        on_delete=models.PROTECT,
        db_column='id_plaza',
        related_name='asignaciones'
    )
    fecha_asignacion = models.DateField(auto_now_add=True)
    estado           = models.CharField(max_length=20, choices=ESTADO_OPCIONES, default='ASIGNADA')
    motivo_rechazo   = models.CharField(max_length=300, null=True, blank=True)
    asignado_por     = models.UUIDField(null=True, blank=True)
    es_automatica    = models.BooleanField(default=True)

    class Meta:
        managed  = False
        db_table = 'practicas\".\"asignacion_internado'

    def __str__(self):
        return f"{self.id_ranking.id_estudiante} → {self.id_plaza.nombre_plaza} ({self.estado})"


class ApelacionInternado(models.Model):
    """
    practicas.apelacion_internado — Apelaciones de estudiantes.
    managed=False — tabla existente en Innotech.
    """
    ESTADO_OPCIONES = [
        ('PRESENTADA',  'Presentada'),
        ('EN_REVISION', 'En Revisión'),
        ('RESUELTA',    'Resuelta'),
        ('DENEGADA',    'Denegada'),
    ]

    id             = models.AutoField(primary_key=True)
    id_estudiante  = models.ForeignKey(
        Estudiante,
        on_delete=models.PROTECT,
        db_column='id_estudiante',
        related_name='apelaciones'
    )
    id_periodo     = models.ForeignKey(
        Periodo,
        on_delete=models.PROTECT,
        db_column='id_periodo',
        null=True, blank=True
    )
    motivo         = models.TextField()
    documentos_url = models.JSONField(null=True, blank=True)
    estado         = models.CharField(max_length=20, choices=ESTADO_OPCIONES, default='PRESENTADA')
    resolucion     = models.TextField(null=True, blank=True)
    resuelto_por   = models.UUIDField(null=True, blank=True)
    creado_en      = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed  = False
        db_table = 'practicas\".\"apelacion_internado'

    def __str__(self):
        return f"{self.id_estudiante} — Apelación {self.estado}"


# ============================================================
# TABLAS DEL ESQUEMA ia
# ============================================================

class ModeloIA(models.Model):
    """
    ia.modelo_ia — Registro del modelo XGBoost desplegado.
    managed=False — tabla existente en Innotech.
    """
    id               = models.AutoField(primary_key=True)
    nombre           = models.CharField(max_length=100)
    tipo             = models.CharField(
        max_length=30,
        choices=[
            ('CLASIFICACION',  'Clasificación'),
            ('REGRESION',      'Regresión'),
            ('RECOMENDACION',  'Recomendación'),
            ('NLP',            'NLP'),
            ('GENERATIVO',     'Generativo'),
        ],
        default='REGRESION'
    )
    version          = models.CharField(max_length=20)
    descripcion      = models.TextField(null=True, blank=True)
    sistema_origen   = models.CharField(max_length=100, null=True, blank=True)
    fecha_despliegue = models.DateField(null=True, blank=True)
    metricas         = models.JSONField(null=True, blank=True)
    activo           = models.BooleanField(default=False)

    class Meta:
        managed     = False
        db_table    = 'ia\".\"modelo_ia'
        unique_together = [['nombre', 'version']]

    def __str__(self):
        return f"{self.nombre} v{self.version} ({'Activo' if self.activo else 'Inactivo'})"


class LogPrediccion(models.Model):
    """
    ia.log_prediccion — Log de cada ejecución del modelo XGBoost.
    Cada predicción queda registrada con input/output en JSONB.
    managed=False — tabla existente en Innotech.
    """
    id           = models.BigAutoField(primary_key=True)
    id_modelo    = models.ForeignKey(
        ModeloIA,
        on_delete=models.PROTECT,
        db_column='id_modelo',
        related_name='logs'
    )
    entidad_tipo = models.CharField(max_length=60, default='estudiante')
    entidad_id   = models.UUIDField()
    input_data   = models.JSONField(null=True, blank=True)
    output_data  = models.JSONField(null=True, blank=True)
    confianza    = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    tiempo_ms    = models.IntegerField(null=True, blank=True)
    creado_en    = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed  = False
        db_table = 'ia\".\"log_prediccion'

    def __str__(self):
        return f"Log {self.id} — {self.entidad_tipo} ({self.creado_en})"