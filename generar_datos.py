# ============================================================
# GENERAR_DATOS.PY — Script de datos sintéticos
# Genera estudiantes y plazas de prueba en la base de datos
# para entrenar y probar el algoritmo XGBoost.
#
# Uso:
#   python generar_datos.py
#
# Requisitos:
#   - Entorno virtual activo (venv)
#   - Docker con PostgreSQL corriendo
#   - Migraciones aplicadas (python manage.py migrate)
# ============================================================

import os
import sys
import django
import random

# Configurar Django antes de importar modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'internado.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

# Importar modelos DESPUÉS de django.setup()
from django.contrib.auth.models import User
from estudiantes.models import Estudiante
from plazas.models import PlazaInternado


# ============================================================
# CONFIGURACIÓN DE LOS DATOS A GENERAR
# ============================================================
TOTAL_ESTUDIANTES    = 30   # Mínimo 2 para XGBoost, 30 para datos realistas
TOTAL_PLAZAS         = 10   # Plazas disponibles para el período
PERIODO              = '2024-1'
SEMILLA_ALEATORIA    = 42   # Para resultados reproducibles

random.seed(SEMILLA_ALEATORIA)


# ============================================================
# DATOS DE PRUEBA — Nombres ecuatorianos realistas
# ============================================================
NOMBRES = [
    'María', 'Juan', 'Ana', 'Carlos', 'Lucía', 'Pedro',
    'Sofía', 'Luis', 'Valentina', 'Diego', 'Isabella', 'Andrés',
    'Camila', 'Sebastián', 'Daniela', 'Miguel', 'Fernanda', 'José',
    'Gabriela', 'David', 'Paula', 'Mateo', 'Natalia', 'Alejandro',
    'Valeria', 'Santiago', 'Andrea', 'Ricardo', 'Paola', 'Jorge',
]

APELLIDOS = [
    'García', 'Rodríguez', 'Martínez', 'López', 'González',
    'Pérez', 'Sánchez', 'Ramírez', 'Torres', 'Flores',
    'Rivera', 'Morales', 'Jiménez', 'Hernández', 'Díaz',
    'Vásquez', 'Romero', 'Alvarado', 'Castillo', 'Mendoza',
    'Reyes', 'Cruz', 'Ortega', 'Guerrero', 'Medina',
    'Ruiz', 'Vargas', 'Suárez', 'Molina', 'Aguilar',
]

ESTADOS_CIVILES = ['soltero', 'casado', 'union_libre', 'divorciado', 'viudo']

UBICACIONES = ['urbana', 'rural', 'periurbana']

INSTITUCIONES = [
    ('Hospital General Enrique Garcés',      'emergencias',      'Quito'),
    ('Hospital Metropolitano',               'cirugia',          'Quito'),
    ('Hospital Pablo Arturo Suárez',         'medicina_interna', 'Quito'),
    ('Hospital Eugenio Espejo',              'clinica',          'Quito'),
    ('Hospital Baca Ortiz',                  'pediatria',        'Quito'),
    ('Hospital Gineco-Obstétrico Isidro Ayora', 'ginecologia',   'Quito'),
    ('Hospital Andrade Marín',               'cirugia',          'Quito'),
    ('Hospital San Francisco de Quito',      'medicina_interna', 'Quito'),
    ('Hospital Vozandes',                    'clinica',          'Quito'),
    ('Hospital Un Canto a la Vida',          'pediatria',        'Quito'),
]


# ============================================================
# FUNCIÓN: Obtener o crear usuario administrador para auditoría
# ============================================================
def obtener_usuario_admin():
    """
    Obtiene el superusuario existente o crea uno temporal
    para que ModelBase pueda registrar la auditoría.
    """
    usuario = User.objects.filter(is_superuser=True).first()
    if not usuario:
        usuario = User.objects.create_superuser(
            username='admin_script',
            email='admin@internado.edu.ec',
            password='Admin123!'
        )
        print('  → Usuario admin_script creado para auditoría del script.')
    return usuario


# ============================================================
# FUNCIÓN: Generar cédula ecuatoriana válida (formato)
# ============================================================
def generar_cedula(indice: int) -> str:
    """Genera una cédula de 10 dígitos única basada en el índice."""
    base   = str(1700000000 + indice).zfill(10)
    return base[:10]


# ============================================================
# FUNCIÓN: Crear estudiantes sintéticos
# ============================================================
def crear_estudiantes():
    """
    Genera TOTAL_ESTUDIANTES estudiantes con datos variados
    para que XGBoost tenga diversidad en las variables.
    Distribuye intencionalmente los perfiles para cubrir
    todos los rangos de prioridad posibles.
    """
    print(f'\n📚 Creando {TOTAL_ESTUDIANTES} estudiantes sintéticos...')

    creados   = 0
    omitidos  = 0

    for i in range(TOTAL_ESTUDIANTES):
        cedula = generar_cedula(i + 1)

        # Omitir si ya existe (ejecuciones repetidas del script)
        if Estudiante.objects.filter(cedula=cedula).exists():
            omitidos += 1
            continue

        nombre   = NOMBRES[i % len(NOMBRES)]
        apellido = APELLIDOS[i % len(APELLIDOS)]

        # --- Distribuir perfiles variados intencionalmente ---

        # Perfil ALTO: buenas notas, muchas cargas, zona rural, situación baja
        if i < 8:
            calificaciones      = round(random.uniform(8.5, 10.0), 2)
            cargas_familiares   = random.randint(2, 5)
            ubicacion           = 'rural'
            situacion_economica = random.randint(1, 2)
            estado_civil        = random.choice(['casado', 'union_libre'])
            nivel_academico     = random.randint(8, 10)
            ingles              = True
            calificaciones_ok   = True

        # Perfil MEDIO: notas medias, cargas variables
        elif i < 18:
            calificaciones      = round(random.uniform(7.0, 8.4), 2)
            cargas_familiares   = random.randint(0, 3)
            ubicacion           = random.choice(UBICACIONES)
            situacion_economica = random.randint(2, 4)
            estado_civil        = random.choice(ESTADOS_CIVILES)
            nivel_academico     = random.randint(6, 9)
            ingles              = True
            calificaciones_ok   = True

        # Perfil BAJO: notas bajas, sin cargas, zona urbana
        elif i < 25:
            calificaciones      = round(random.uniform(5.0, 6.9), 2)
            cargas_familiares   = random.randint(0, 1)
            ubicacion           = 'urbana'
            situacion_economica = random.randint(3, 5)
            estado_civil        = 'soltero'
            nivel_academico     = random.randint(5, 7)
            ingles              = True
            calificaciones_ok   = True

        # Perfil NO HABILITADO: no cumplen requisitos (para probar validación)
        else:
            calificaciones      = round(random.uniform(6.0, 9.0), 2)
            cargas_familiares   = random.randint(0, 3)
            ubicacion           = random.choice(UBICACIONES)
            situacion_economica = random.randint(1, 5)
            estado_civil        = random.choice(ESTADOS_CIVILES)
            nivel_academico     = random.randint(5, 10)
            ingles              = random.choice([True, False])
            calificaciones_ok   = False   # Calificaciones NO cerradas

        estudiante = Estudiante(
            cedula                   = cedula,
            nombres                  = nombre,
            apellidos                = f'{apellido} {APELLIDOS[(i + 5) % len(APELLIDOS)]}',
            correo                   = f'{nombre.lower()}.{apellido.lower()}{i}@universidad.edu.ec',
            telefono                 = f'09{random.randint(10000000, 99999999)}',
            estado_civil             = estado_civil,
            cargas_familiares        = cargas_familiares,
            ubicacion_geografica     = ubicacion,
            situacion_economica      = situacion_economica,
            calificaciones           = calificaciones,
            nivel_academico          = nivel_academico,
            modulos_ingles_aprobados = ingles,
            calificaciones_cerradas  = calificaciones_ok,
        )
        estudiante.save()
        creados += 1

    print(f'  ✓ {creados} estudiantes creados.')
    if omitidos:
        print(f'  → {omitidos} ya existían, omitidos.')

    # Mostrar resumen de habilitados vs no habilitados
    habilitados = Estudiante.objects.filter(
        modulos_ingles_aprobados=True,
        calificaciones_cerradas=True,
    ).count()
    print(f'  ✓ {habilitados} estudiantes habilitados para el ranking.')
    print(f'  ✓ {Estudiante.objects.count() - habilitados} no habilitados (para probar validación).')


# ============================================================
# FUNCIÓN: Crear plazas de internado
# ============================================================
def crear_plazas():
    """
    Genera TOTAL_PLAZAS plazas disponibles en el período.
    Usa hospitales reales de Ecuador para datos realistas.
    """
    print(f'\n🏥 Creando {TOTAL_PLAZAS} plazas de internado...')

    creadas  = 0
    omitidas = 0

    for i, (institucion, area, ciudad) in enumerate(INSTITUCIONES[:TOTAL_PLAZAS]):
        codigo = f'PLAZA-{PERIODO}-{str(i + 1).zfill(3)}'

        if PlazaInternado.objects.filter(codigo=codigo).exists():
            omitidas += 1
            continue

        plaza = PlazaInternado(
            codigo      = codigo,
            institucion = institucion,
            area        = area,
            ciudad      = ciudad,
            estado      = 'disponible',
            periodo     = PERIODO,
        )
        plaza.save()
        creadas += 1

    print(f'  ✓ {creadas} plazas creadas para el período {PERIODO}.')
    if omitidas:
        print(f'  → {omitidas} ya existían, omitidas.')


# ============================================================
# FUNCIÓN: Mostrar resumen final
# ============================================================
def mostrar_resumen():
    """Muestra un resumen de los datos cargados en la BD."""
    print('\n' + '=' * 55)
    print('  RESUMEN DE DATOS CARGADOS EN POSTGRESQL')
    print('=' * 55)
    print(f'  Total estudiantes:     {Estudiante.objects.count()}')
    print(f'  Estudiantes activos:   {Estudiante.objects.filter(status=True).count()}')
    print(f'  Habilitados ranking:   {Estudiante.objects.filter(modulos_ingles_aprobados=True, calificaciones_cerradas=True).count()}')
    print(f'  Total plazas:          {PlazaInternado.objects.count()}')
    print(f'  Plazas disponibles:    {PlazaInternado.objects.filter(estado="disponible").count()}')
    print('=' * 55)
    print('\n  Próximos pasos:')
    print('  1. Abre http://127.0.0.1:8000/api/docs/')
    print('  2. Prueba GET /api/v1/ranking/generar/')
    print('  3. Prueba POST /api/v1/ranking/asignar/ con {"periodo": "2024-1"}')
    print('=' * 55 + '\n')


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================
if __name__ == '__main__':
    print('\n' + '=' * 55)
    print('  GENERADOR DE DATOS SINTÉTICOS — INTERNADO API')
    print('=' * 55)

    try:
        obtener_usuario_admin()
        crear_estudiantes()
        crear_plazas()
        mostrar_resumen()
        print('  ✅ Datos generados correctamente.\n')

    except Exception as e:
        print(f'\n  ❌ Error: {e}')
        print('  Verifica que:')
        print('  1. Docker esté corriendo (docker compose ps)')
        print('  2. Las migraciones estén aplicadas (python manage.py migrate)')
        print('  3. El archivo .env tenga las credenciales correctas\n')
        sys.exit(1)
