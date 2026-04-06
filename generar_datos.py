# ============================================================
# GENERAR_DATOS.PY — Script de datos sintéticos
# Inserta directamente en tablas de la BD Innotech:
#   core.persona
#   estudiantil.estudiante
#   estudiantil.situacion_economica
#   estudiantil.carga_familiar
#   practicas.requisito_habilitante  ← crea primero
#   practicas.verificacion_requisito
#   practicas.institucion_receptora
#   practicas.plaza_practica
#   academico.periodo (verifica/crea)
#
# Uso:
#   python generar_datos.py
# ============================================================

import os
import sys
import uuid
import random
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'internado.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection

random.seed(42)

# ============================================================
# CONFIGURACIÓN
# ============================================================
TOTAL_ESTUDIANTES = 30
TOTAL_PLAZAS      = 10
PERIODO_CODIGO    = '2024-1'
CARRERA_ID        = 1   # ISI — Ingeniería en Sistemas Inteligentes

# ============================================================
# DATOS DE PRUEBA
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
INSTITUCIONES = [
    ('Hospital General Enrique Garcés',          'emergencias'),
    ('Hospital Metropolitano',                   'cirugia'),
    ('Hospital Pablo Arturo Suárez',             'medicina_interna'),
    ('Hospital Eugenio Espejo',                  'clinica'),
    ('Hospital Baca Ortiz',                      'pediatria'),
    ('Hospital Gineco-Obstétrico Isidro Ayora',  'ginecologia'),
    ('Hospital Andrade Marín',                   'cirugia'),
    ('Hospital San Francisco de Quito',          'medicina_interna'),
    ('Hospital Vozandes',                        'clinica'),
    ('Hospital Un Canto a la Vida',              'pediatria'),
]
NIVELES_POBREZA = ['EXTREMA', 'BAJA', 'MEDIA', 'ALTA']
PARENTESCOS     = ['HIJO', 'PADRE', 'MADRE', 'CONYUGUE', 'HERMANO']


def ejecutar(sql, params=None):
    """Ejecuta SQL y retorna las filas."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        try:
            return cursor.fetchall()
        except Exception:
            return []


def obtener_periodo_id():
    """Obtiene o crea el período en academico.periodo."""
    rows = ejecutar(
        "SELECT id FROM academico.periodo WHERE codigo = %s",
        [PERIODO_CODIGO]
    )
    if not rows:
        ejecutar(
            """
            INSERT INTO academico.periodo(nombre, codigo, fecha_inicio, fecha_fin, activo, en_curso)
            VALUES (%s, %s, %s, %s, TRUE, FALSE)
            """,
            [f'Período {PERIODO_CODIGO}', PERIODO_CODIGO, date(2024, 3, 1), date(2024, 8, 31)]
        )
        rows = ejecutar(
            "SELECT id FROM academico.periodo WHERE codigo = %s",
            [PERIODO_CODIGO]
        )
    return rows[0][0]


def obtener_tipo_identificacion_id():
    """Obtiene el ID del tipo 'CI' desde core.tipo_identificacion."""
    rows = ejecutar("SELECT id FROM core.tipo_identificacion WHERE codigo = 'CI'")
    return rows[0][0] if rows else 1


def obtener_tipo_institucion_id():
    """Obtiene el ID del tipo 'PUBLICA' desde practicas.tipo_institucion_receptora."""
    rows = ejecutar(
        "SELECT id FROM practicas.tipo_institucion_receptora WHERE nombre = 'PUBLICA'"
    )
    return rows[0][0] if rows else 1


def obtener_modalidad_internado_id():
    """Obtiene el ID de 'INTERNADO' desde practicas.modalidad_practica."""
    rows = ejecutar(
        "SELECT id FROM practicas.modalidad_practica WHERE nombre = 'INTERNADO'"
    )
    return rows[0][0] if rows else 1


def crear_requisitos_habilitantes():
    """
    Crea los requisitos habilitantes en practicas.requisito_habilitante.
    Son el prerequisito para poder insertar en verificacion_requisito.
    Retorna (id_ingles, id_calificaciones).
    """
    print('\n Verificando requisitos habilitantes...')

    # Requisito 1: Módulos de inglés
    rows = ejecutar(
        "SELECT id FROM practicas.requisito_habilitante WHERE tipo = 'INGLES' AND id_carrera = %s",
        [CARRERA_ID]
    )
    if rows:
        id_ingles = rows[0][0]
        print(f'  → Requisito INGLES ya existe (ID: {id_ingles})')
    else:
        ejecutar(
            """
            INSERT INTO practicas.requisito_habilitante(id_carrera, nombre, descripcion, tipo, activo)
            VALUES (%s, %s, %s, 'INGLES', TRUE)
            """,
            [CARRERA_ID, 'Módulos de Inglés Aprobados',
             'El estudiante debe haber aprobado todos los módulos de inglés requeridos']
        )
        rows = ejecutar(
            "SELECT id FROM practicas.requisito_habilitante WHERE tipo = 'INGLES' AND id_carrera = %s",
            [CARRERA_ID]
        )
        id_ingles = rows[0][0]
        print(f'  ✓ Requisito INGLES creado (ID: {id_ingles})')

    # Requisito 2: Calificaciones cerradas
    rows = ejecutar(
        "SELECT id FROM practicas.requisito_habilitante WHERE tipo = 'CALIFICACIONES' AND id_carrera = %s",
        [CARRERA_ID]
    )
    if rows:
        id_calificaciones = rows[0][0]
        print(f'  → Requisito CALIFICACIONES ya existe (ID: {id_calificaciones})')
    else:
        ejecutar(
            """
            INSERT INTO practicas.requisito_habilitante(id_carrera, nombre, descripcion, tipo, activo)
            VALUES (%s, %s, %s, 'CALIFICACIONES', TRUE)
            """,
            [CARRERA_ID, 'Calificaciones del Período Cerradas',
             'El estudiante debe tener todas las calificaciones del período cerradas y aprobadas']
        )
        rows = ejecutar(
            "SELECT id FROM practicas.requisito_habilitante WHERE tipo = 'CALIFICACIONES' AND id_carrera = %s",
            [CARRERA_ID]
        )
        id_calificaciones = rows[0][0]
        print(f'  ✓ Requisito CALIFICACIONES creado (ID: {id_calificaciones})')

    return id_ingles, id_calificaciones


def crear_estudiantes(periodo_id, tipo_id_ci, id_ingles, id_calificaciones):
    """
    Inserta estudiantes en core.persona y estudiantil.estudiante.
    Crea situación económica, cargas familiares y verificaciones.
    """
    print(f'\n Creando {TOTAL_ESTUDIANTES} estudiantes en tablas Innotech...')
    creados = omitidos = 0

    for i in range(TOTAL_ESTUDIANTES):
        cedula = f'17{str(i + 1).zfill(8)}'

        # Verificar si ya existe
        rows = ejecutar(
            "SELECT id FROM core.persona WHERE numero_identificacion = %s",
            [cedula]
        )
        if rows:
            omitidos += 1
            continue

        nombre    = NOMBRES[i % len(NOMBRES)]
        apellido  = APELLIDOS[i % len(APELLIDOS)]
        apellido2 = APELLIDOS[(i + 5) % len(APELLIDOS)]

        # Perfiles variados para diversidad en el ranking
        if i < 8:
            nivel      = random.randint(8, 10)
            nivel_ec   = 'EXTREMA'
            n_cargas   = random.randint(2, 5)
            habilitado = True
        elif i < 18:
            nivel      = random.randint(6, 9)
            nivel_ec   = random.choice(['BAJA', 'MEDIA'])
            n_cargas   = random.randint(0, 3)
            habilitado = True
        elif i < 25:
            nivel      = random.randint(5, 7)
            nivel_ec   = random.choice(['MEDIA', 'ALTA'])
            n_cargas   = random.randint(0, 1)
            habilitado = True
        else:
            nivel      = random.randint(5, 10)
            nivel_ec   = random.choice(NIVELES_POBREZA)
            n_cargas   = random.randint(0, 3)
            habilitado = False

        # 1. Insertar en core.persona
        persona_id = str(uuid.uuid4())
        ejecutar(
            """
            INSERT INTO core.persona(
                id, tipo_identificacion, numero_identificacion,
                primer_nombre, primer_apellido, segundo_apellido,
                email_institucional, telefono_movil, activo
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """,
            [
                persona_id, tipo_id_ci, cedula,
                nombre, apellido, apellido2,
                f'{nombre.lower()}{i}@ube.edu.ec',
                f'09{random.randint(10000000, 99999999)}',
            ]
        )

        # 2. Insertar en estudiantil.estudiante
        est_id = str(uuid.uuid4())
        ejecutar(
            """
            INSERT INTO estudiantil.estudiante(
                id, id_persona, id_carrera, codigo_estudiante,
                fecha_ingreso, nivel_actual, estado
            ) VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVO')
            """,
            [est_id, persona_id, CARRERA_ID,
             f'EST-{str(i+1).zfill(4)}', date(2020, 3, 1), nivel]
        )

        # 3. Insertar situación económica
        ejecutar(
            """
            INSERT INTO estudiantil.situacion_economica(
                id_estudiante, id_periodo, ingreso_familiar,
                numero_miembros_hogar, nivel_pobreza,
                tiene_bono_desarrollo, trabaja
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            [
                est_id, periodo_id,
                round(random.uniform(200, 2000), 2),
                random.randint(2, 8),
                nivel_ec,
                nivel_ec == 'EXTREMA',
                random.choice([True, False]),
            ]
        )

        # 4. Insertar cargas familiares
        for _ in range(n_cargas):
            ejecutar(
                """
                INSERT INTO estudiantil.carga_familiar(
                    id_estudiante, parentesco, edad, es_dependiente
                ) VALUES (%s, %s, %s, TRUE)
                """,
                [est_id, random.choice(PARENTESCOS), random.randint(0, 70)]
            )

        # 5. Insertar verificaciones de requisitos habilitantes
        if habilitado:
            for req_id in [id_ingles, id_calificaciones]:
                ejecutar(
                    """
                    INSERT INTO practicas.verificacion_requisito(
                        id_estudiante, id_requisito, id_periodo, cumple
                    ) VALUES (%s, %s, %s, TRUE)
                    ON CONFLICT (id_estudiante, id_requisito, id_periodo) DO NOTHING
                    """,
                    [est_id, req_id, periodo_id]
                )

        creados += 1

    print(f'  ✓ {creados} estudiantes creados.')
    if omitidos:
        print(f'  → {omitidos} ya existían, omitidos.')

    # Contar habilitados usando los IDs correctos
    rows = ejecutar(
        """
        SELECT COUNT(DISTINCT e.id)
        FROM estudiantil.estudiante e
        JOIN practicas.verificacion_requisito vi
            ON vi.id_estudiante = e.id AND vi.id_requisito = %s AND vi.cumple = TRUE
        JOIN practicas.verificacion_requisito vc
            ON vc.id_estudiante = e.id AND vc.id_requisito = %s AND vc.cumple = TRUE
        """,
        [id_ingles, id_calificaciones]
    )
    print(f'  ✓ {rows[0][0]} estudiantes habilitados (inglés + calificaciones).')
    print(f'  ✓ {TOTAL_ESTUDIANTES - rows[0][0]} no habilitados.')


def crear_plazas(periodo_id, tipo_inst_id, modalidad_id):
    """Inserta instituciones y plazas en practicas.*"""
    print(f'\n Creando {TOTAL_PLAZAS} instituciones y plazas...')
    creadas = omitidas = 0

    for nombre_inst, area in INSTITUCIONES[:TOTAL_PLAZAS]:
        # Crear o recuperar institución
        rows = ejecutar(
            "SELECT id FROM practicas.institucion_receptora WHERE nombre = %s",
            [nombre_inst]
        )
        if rows:
            inst_id = rows[0][0]
        else:
            ejecutar(
                """
                INSERT INTO practicas.institucion_receptora(id_tipo, nombre, activa)
                VALUES (%s, %s, TRUE)
                """,
                [tipo_inst_id, nombre_inst]
            )
            rows    = ejecutar(
                "SELECT id FROM practicas.institucion_receptora WHERE nombre = %s",
                [nombre_inst]
            )
            inst_id = rows[0][0]

        # Verificar si ya existe plaza para este período
        rows = ejecutar(
            """
            SELECT id FROM practicas.plaza_practica
            WHERE id_institucion = %s AND id_periodo = %s
            """,
            [inst_id, periodo_id]
        )
        if rows:
            omitidas += 1
            continue

        cupo = random.randint(1, 3)
        ejecutar(
            """
            INSERT INTO practicas.plaza_practica(
                id_institucion, id_carrera, id_modalidad, id_periodo,
                nombre_plaza, cupo_total, cupo_disponible, activa
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            """,
            [
                inst_id, CARRERA_ID, modalidad_id, periodo_id,
                f'Plaza {area.replace("_", " ").title()} — {nombre_inst}',
                cupo, cupo,
            ]
        )
        creadas += 1

    print(f'  ✓ {creadas} plazas creadas para el período {PERIODO_CODIGO}.')
    if omitidas:
        print(f'  → {omitidas} ya existían, omitidas.')


def mostrar_resumen(periodo_id):
    """Muestra resumen consultando directamente las tablas Innotech."""
    total_est  = ejecutar("SELECT COUNT(*) FROM estudiantil.estudiante")[0][0]
    total_sit  = ejecutar("SELECT COUNT(*) FROM estudiantil.situacion_economica")[0][0]
    total_car  = ejecutar("SELECT COUNT(*) FROM estudiantil.carga_familiar")[0][0]
    total_req  = ejecutar("SELECT COUNT(*) FROM practicas.requisito_habilitante")[0][0]
    total_ver  = ejecutar("SELECT COUNT(*) FROM practicas.verificacion_requisito")[0][0]
    total_inst = ejecutar("SELECT COUNT(*) FROM practicas.institucion_receptora")[0][0]
    total_plaz = ejecutar(
        "SELECT COUNT(*) FROM practicas.plaza_practica WHERE id_periodo = %s",
        [periodo_id]
    )[0][0]
    total_cupo = ejecutar(
        "SELECT COALESCE(SUM(cupo_disponible), 0) FROM practicas.plaza_practica WHERE id_periodo = %s AND activa = TRUE",
        [periodo_id]
    )[0][0]

    print('\n' + '=' * 60)
    print('  RESUMEN — Tablas Innotech pobladas correctamente')
    print('=' * 60)
    print(f'  estudiantil.estudiante:              {total_est}')
    print(f'  estudiantil.situacion_economica:     {total_sit}')
    print(f'  estudiantil.carga_familiar:          {total_car}')
    print(f'  practicas.requisito_habilitante:     {total_req}')
    print(f'  practicas.verificacion_requisito:    {total_ver}')
    print(f'  practicas.institucion_receptora:     {total_inst}')
    print(f'  practicas.plaza_practica ({PERIODO_CODIGO}):  {total_plaz}')
    print(f'  Cupo total disponible:               {total_cupo}')
    print('=' * 60)
    print('\n  Próximos pasos:')
    print('  1. python manage.py runserver')
    print('  2. GET  /api/v1/ranking/generar/')
    print(f'  3. POST /api/v1/ranking/asignar/  →  {{"periodo":"{PERIODO_CODIGO}"}}')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('  GENERADOR DE DATOS — Tablas Innotech (managed=False)')
    print('  Inserta en: core, estudiantil, practicas')
    print('=' * 60)
    try:
        periodo_id   = obtener_periodo_id()
        tipo_id_ci   = obtener_tipo_identificacion_id()
        tipo_inst_id = obtener_tipo_institucion_id()
        modalidad_id = obtener_modalidad_internado_id()

        print(f'  Período ID: {periodo_id} ({PERIODO_CODIGO})')

        id_ingles, id_calificaciones = crear_requisitos_habilitantes()
        crear_estudiantes(periodo_id, tipo_id_ci, id_ingles, id_calificaciones)
        crear_plazas(periodo_id, tipo_inst_id, modalidad_id)
        mostrar_resumen(periodo_id)

        print('  ✅ Datos generados correctamente en la BD Innotech.\n')

    except Exception as e:
        print(f'\n  ❌ Error: {e}')
        import traceback
        traceback.print_exc()
        print('\n  Verifica que:')
        print('  1. Docker esté corriendo (docker compose ps)')
        print('  2. El .env tenga DB_NAME=innotech_db')
        print('  3. El search_path incluya todos los esquemas\n')
        sys.exit(1)