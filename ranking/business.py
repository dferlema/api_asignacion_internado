# ============================================================
# BUSINESS.PY — App Ranking (Capa 4: Lógica de Negocio + IA)
# Lee desde tablas Innotech directamente (managed=False).
# Escribe en practicas.ranking_internado, asignacion_internado
# e ia.log_prediccion.
#
# SHAP: se usa pred_contribs=True nativo de XGBoost (v2.1.3+).
# No requiere instalar la librería 'shap' por separado.
# Cada predicción guarda su explicación SHAP en output_data
# de ia.log_prediccion para respaldo legal ante apelaciones.
# ============================================================

import time
import numpy as np
import pandas as pd
from xgboost import XGBRegressor, DMatrix
from sklearn.preprocessing import LabelEncoder
from django.db import transaction, connection

from estudiantes.models import Estudiante, Periodo
from plazas.models import (
    PlazaPractica,
    RankingInternado,
    AsignacionInternado,
    ModeloIA,
    LogPrediccion,
)

# Nombres de las variables en el mismo orden que _variables_entrada()
NOMBRES_VARIABLES = [
    'cargas_familiares',
    'ubicacion_geografica',
    'situacion_economica',
    'calificaciones',
    'nivel_academico',
    'es_zona_rural',
    'necesidad_economica',
]


class RankingBusiness:
    """
    Lógica de negocio del ranking con XGBoost + SHAP.

    SHAP (SHapley Additive exPlanations) explica cuánto contribuyó
    cada variable al puntaje final de cada estudiante.
    Esto es fundamental para:
    - Responder apelaciones con evidencia numérica
    - Cumplir con transparencia algorítmica
    - Auditorías institucionales y legales
    """

    # Pesos según practicas.criterio_asignacion del SQL de Innotech
    PESOS = {
        'calificaciones':      0.30,
        'cargas_familiares':   0.25,
        'necesidad_economica': 0.20,
        'ubicacion_rural':     0.15,
        'nivel_academico':     0.10,
    }

    PARAMETROS_MODELO = {
        'n_estimators':  100,
        'learning_rate': 0.1,
        'max_depth':     4,
        'subsample':     0.8,
        'random_state':  42,
        'verbosity':     0,
    }

    NOMBRE_MODELO  = 'XGBoost-Internado'
    VERSION_MODELO = '1.0.0'

    def __init__(self):
        self.modelo           = XGBRegressor(**self.PARAMETROS_MODELO)
        self.enc_ubicacion    = LabelEncoder()
        self.modelo_entrenado = False
        self._modelo_ia       = None
        self._X_entrenado     = None   # Guardado para SHAP posterior

    # ----------------------------------------------------------
    # MÉTODO AUXILIAR: IDs reales de requisitos habilitantes
    # ----------------------------------------------------------

    @staticmethod
    def _obtener_ids_requisitos():
        """
        Consulta practicas.requisito_habilitante y retorna los IDs
        reales de INGLES y CALIFICACIONES.
        No usa valores hardcodeados — lee siempre desde la BD.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, tipo
                FROM practicas.requisito_habilitante
                WHERE tipo IN ('INGLES', 'CALIFICACIONES')
                  AND activo = TRUE
                ORDER BY tipo
                """
            )
            rows = cursor.fetchall()

        id_ingles         = next((r[0] for r in rows if r[1] == 'INGLES'), None)
        id_calificaciones = next((r[0] for r in rows if r[1] == 'CALIFICACIONES'), None)

        if not id_ingles or not id_calificaciones:
            raise ValueError(
                'No se encontraron los requisitos habilitantes en '
                'practicas.requisito_habilitante (INGLES y CALIFICACIONES). '
                'Ejecute generar_datos.py primero.'
            )
        return id_ingles, id_calificaciones

    # ----------------------------------------------------------
    # OBTENER ESTUDIANTES HABILITADOS
    # ----------------------------------------------------------

    def _obtener_habilitados(self):
        """
        Retorna estudiantes ACTIVOS que tienen ambos requisitos
        aprobados en practicas.verificacion_requisito.
        Usa id_requisito (FK entero real de Innotech).
        """
        id_ingles, id_calificaciones = self._obtener_ids_requisitos()

        con_ingles = Estudiante.objects.filter(
            verificaciones_requisitos__id_requisito=id_ingles,
            verificaciones_requisitos__cumple=True,
        ).values('id')

        con_calificaciones = Estudiante.objects.filter(
            verificaciones_requisitos__id_requisito=id_calificaciones,
            verificaciones_requisitos__cumple=True,
        ).values('id')

        return Estudiante.objects.filter(
            estado='ACTIVO',
            id__in=con_ingles,
        ).filter(
            id__in=con_calificaciones,
        ).select_related(
            'id_persona__id_parroquia',
            'id_carrera',
        ).prefetch_related(
            'situaciones_economicas',
            'cargas_familiares',
        )

    # ----------------------------------------------------------
    # PREPARAR DATOS PARA XGBOOST
    # ----------------------------------------------------------

    def _preparar_df(self, qs):
        """
        Convierte QuerySet de estudiantes a DataFrame de pandas.
        Usa las propiedades del modelo para resolver cada variable
        desde las tablas relacionadas de Innotech.
        """
        registros = []
        for e in qs:
            promedio = e.promedio_academico
            registros.append({
                'id':                  str(e.id),
                'cargas_familiares':   e.total_cargas_familiares,
                'ubicacion':           e.ubicacion_tipo or 'URBANA',
                'situacion_economica': e.nivel_situacion_economica,
                'calificaciones':      float(promedio) if promedio else 7.0,
                'nivel_academico':     e.nivel_actual or 1,
            })
        return pd.DataFrame(registros)

    def _codificar(self, df):
        """Codifica variables categóricas a numéricas para XGBoost."""
        df = df.copy()
        df['ubicacion_cod']       = self.enc_ubicacion.fit_transform(df['ubicacion'])
        df['es_rural']            = (df['ubicacion'] == 'RURAL').astype(int)
        df['necesidad_economica'] = 5 - df['situacion_economica']
        return df

    def _puntaje_base(self, df):
        """Puntaje ponderado con pesos institucionales (0-10)."""
        cal = df['calificaciones'] / 10.0
        car = df['cargas_familiares'] / df['cargas_familiares'].max().clip(1)
        nec = df['necesidad_economica'] / 4.0
        niv = df['nivel_academico'] / df['nivel_academico'].max().clip(1)
        rur = df['es_rural'].astype(float)
        return (
            cal * self.PESOS['calificaciones']      +
            car * self.PESOS['cargas_familiares']   +
            nec * self.PESOS['necesidad_economica'] +
            rur * self.PESOS['ubicacion_rural']     +
            niv * self.PESOS['nivel_academico']
        ) * 10

    def _variables_entrada(self, df):
        """Retorna las 7 columnas de entrada del modelo XGBoost."""
        return df[[
            'cargas_familiares', 'ubicacion_cod', 'situacion_economica',
            'calificaciones', 'nivel_academico', 'es_rural', 'necesidad_economica',
        ]]

    # ----------------------------------------------------------
    # SHAP — VALORES DE CONTRIBUCIÓN POR ESTUDIANTE
    # ----------------------------------------------------------

    def calcular_shap(self, X: pd.DataFrame) -> np.ndarray:
        """
        Calcula los valores SHAP usando pred_contribs=True nativo
        de XGBoost. No requiere instalar la librería 'shap'.

        Los valores SHAP indican cuánto contribuyó cada variable
        al puntaje final de cada estudiante respecto al valor base
        (promedio del modelo).

        Args:
            X (pd.DataFrame): Variables de entrada ya codificadas.

        Returns:
            np.ndarray: Matriz de shape (n_estudiantes, n_variables+1).
                        La última columna es el valor base (bias).

        Raises:
            ValueError: Si el modelo no fue entrenado primero.
        """
        if not self.modelo_entrenado:
            raise ValueError('Ejecute generar_ranking() primero.')

        dmatrix = DMatrix(X)
        # pred_contribs=True retorna contribuciones SHAP por árbol
        # shape: (n_muestras, n_features + 1) — última col es bias
        contribs = self.modelo.get_booster().predict(
            dmatrix, pred_contribs=True
        )
        return contribs

    def explicacion_shap_estudiante(
        self, estudiante_id: str, X: pd.DataFrame, df_ids: pd.Series
    ) -> dict:
        """
        Genera la explicación SHAP para un estudiante específico.

        Args:
            estudiante_id (str): UUID del estudiante.
            X (pd.DataFrame):   Variables de entrada del ranking completo.
            df_ids (pd.Series): IDs en el mismo orden que X.

        Returns:
            dict con contribuciones SHAP por variable y valor base.
        """
        contribs = self.calcular_shap(X)
        idx      = df_ids[df_ids == estudiante_id].index

        if len(idx) == 0:
            raise ValueError(f'Estudiante {estudiante_id} no encontrado en el ranking.')

        fila       = contribs[idx[0]]
        valor_base = float(fila[-1])   # último elemento = bias/valor_base
        shap_vals  = fila[:-1]         # primeros n = contribuciones por variable

        contribuciones = {
            NOMBRES_VARIABLES[i]: round(float(shap_vals[i]), 4)
            for i in range(len(NOMBRES_VARIABLES))
        }

        # Ordenar de mayor a menor contribución (absoluta)
        contribuciones_ordenadas = dict(
            sorted(contribuciones.items(), key=lambda x: abs(x[1]), reverse=True)
        )

        return {
            'valor_base':               round(valor_base, 4),
            'contribuciones_por_variable': contribuciones_ordenadas,
            'puntaje_total_shap':       round(
                valor_base + sum(shap_vals), 4
            ),
            'interpretacion': [
                {
                    'variable':      nombre,
                    'contribucion':  val,
                    'impacto':       'positivo' if val > 0 else 'negativo' if val < 0 else 'neutro',
                    'magnitud':      'alta' if abs(val) > 0.5 else 'media' if abs(val) > 0.1 else 'baja',
                }
                for nombre, val in contribuciones_ordenadas.items()
                if abs(val) > 0.001  # omitir contribuciones despreciables
            ],
        }

    def importancia_variables(self) -> dict:
        """Retorna importancia global de cada variable según XGBoost."""
        if not self.modelo_entrenado:
            raise ValueError('Ejecute generar_ranking() primero.')
        nombres = NOMBRES_VARIABLES
        return {
            n: round(float(i) * 100, 2)
            for n, i in zip(nombres, self.modelo.feature_importances_)
        }

    # ----------------------------------------------------------
    # OBTENER MODELO IA
    # ----------------------------------------------------------

    def _obtener_o_crear_modelo_ia(self):
        """Obtiene o crea el registro del modelo en ia.modelo_ia."""
        modelo_ia, _ = ModeloIA.objects.get_or_create(
            nombre=self.NOMBRE_MODELO,
            version=self.VERSION_MODELO,
            defaults={
                'tipo':           'REGRESION',
                'descripcion':    'XGBoost para ranking de internado — Sistema 17',
                'sistema_origen': 'SISTEMA_17_INTERNADO',
                'activo':         True,
            }
        )
        return modelo_ia

    # ----------------------------------------------------------
    # GENERAR RANKING (ahora incluye SHAP en cada predicción)
    # ----------------------------------------------------------

    def generar_ranking(self, periodo_codigo: str = None) -> list:
        """
        Ejecuta XGBoost sobre estudiantes habilitados de Innotech.
        Ahora incluye valores SHAP individuales en cada entrada del
        ranking y los guarda en ia.log_prediccion.output_data.

        Args:
            periodo_codigo (str): Código del período (ej: '2024-1').

        Returns:
            list: Ranking ordenado por puntaje con explicaciones SHAP.

        Raises:
            ValueError: Si no hay suficientes estudiantes habilitados.
        """
        qs    = self._obtener_habilitados()
        total = qs.count()
        if total < 2:
            raise ValueError(
                f'Se necesitan al menos 2 estudiantes habilitados. '
                f'Actualmente hay {total} en estudiantil.estudiante '
                f'con verificaciones aprobadas en practicas.verificacion_requisito. '
                f'Ejecute generar_datos.py para cargar datos de prueba.'
            )

        # --- Preparar datos y entrenar XGBoost ---
        inicio_ms          = int(time.time() * 1000)
        df                 = self._preparar_df(qs)
        df                 = self._codificar(df)
        df['puntaje_base'] = self._puntaje_base(df)
        X                  = self._variables_entrada(df)
        y                  = df['puntaje_base']

        self.modelo.fit(X, y)
        self.modelo_entrenado = True
        self._X_entrenado     = X.copy()   # Guardar para SHAP posterior

        df['puntaje_xgboost'] = self.modelo.predict(X)
        tiempo_ms             = int(time.time() * 1000) - inicio_ms

        # --- Calcular SHAP para todos los estudiantes ---
        contribs_shap = self.calcular_shap(X)

        df             = df.sort_values('puntaje_xgboost', ascending=False).reset_index(drop=True)
        df['posicion'] = df.index + 1

        # --- Construir resultados con SHAP ---
        self._modelo_ia = self._obtener_o_crear_modelo_ia()
        est_dict        = {str(e.id): e for e in qs}

        # Mapa de posición original (antes de ordenar) para acceder a SHAP
        id_a_idx_original = {row['id']: idx for idx, row in df.reset_index().iterrows()}

        resultado = []

        for orden_actual, (_, r) in enumerate(df.iterrows()):
            est     = est_dict[r['id']]
            puntaje = round(float(r['puntaje_xgboost']), 4)

            # --- Extraer SHAP de este estudiante ---
            # Buscar índice original en X (antes del sort)
            idx_original    = X.index[df.index[orden_actual]]
            fila_shap       = contribs_shap[idx_original]
            valor_base_shap = round(float(fila_shap[-1]), 4)
            shap_por_var    = {
                NOMBRES_VARIABLES[i]: round(float(fila_shap[i]), 4)
                for i in range(len(NOMBRES_VARIABLES))
            }
            shap_ordenado = dict(
                sorted(shap_por_var.items(), key=lambda x: abs(x[1]), reverse=True)
            )

            detalle = {
                'calificaciones':      float(r['calificaciones']),
                'cargas_familiares':   int(r['cargas_familiares']),
                'situacion_economica': int(r['situacion_economica']),
                'ubicacion':           r['ubicacion'],
                'nivel_academico':     int(r['nivel_academico']),
                'puntaje_base':        round(float(r['puntaje_base']), 4),
                'pesos_utilizados':    self.PESOS,
            }

            explicacion_shap = {
                'valor_base':                  valor_base_shap,
                'contribuciones_por_variable': shap_ordenado,
                'variable_mas_influyente':     max(shap_por_var, key=lambda k: abs(shap_por_var[k])),
                'interpretacion': [
                    {
                        'variable':     nombre,
                        'contribucion': val,
                        'impacto':      'positivo' if val > 0 else 'negativo' if val < 0 else 'neutro',
                        'magnitud':     'alta' if abs(val) > 0.5 else 'media' if abs(val) > 0.1 else 'baja',
                    }
                    for nombre, val in shap_ordenado.items()
                    if abs(val) > 0.001
                ],
            }

            # --- Registrar en ia.log_prediccion con SHAP ---
            LogPrediccion.objects.create(
                id_modelo    = self._modelo_ia,
                entidad_tipo = 'estudiante',
                entidad_id   = est.id,
                input_data   = {
                    'calificaciones':      float(r['calificaciones']),
                    'cargas_familiares':   int(r['cargas_familiares']),
                    'ubicacion':           r['ubicacion'],
                    'situacion_economica': int(r['situacion_economica']),
                    'nivel_academico':     int(r['nivel_academico']),
                },
                output_data = {
                    'puntaje_xgboost':  puntaje,
                    'posicion':         int(r['posicion']),
                    'shap':             explicacion_shap,   # ← SHAP guardado en BD
                },
                confianza = round(puntaje / 10, 4),
                tiempo_ms = tiempo_ms,
            )

            resultado.append({
                'posicion':            int(r['posicion']),
                'estudiante_id':       str(est.id),
                'nombre_completo':     est.nombre_completo,
                'cedula':              est.cedula,
                'calificaciones':      float(r['calificaciones']),
                'cargas_familiares':   int(r['cargas_familiares']),
                'situacion_economica': int(r['situacion_economica']),
                'ubicacion':           r['ubicacion'],
                'nivel_academico':     int(r['nivel_academico']),
                'puntaje_xgboost':     puntaje,
                'detalle_puntaje':     detalle,
                'explicacion_shap':    explicacion_shap,   # ← SHAP en la respuesta
            })

        return resultado

    # ----------------------------------------------------------
    # RESOLVER ESTUDIANTE — por UUID, cédula o nombre
    # ----------------------------------------------------------

    @staticmethod
    def resolver_estudiante(
        estudiante_id: str = None,
        cedula: str = None,
        nombre: str = None,
    ) -> str:
        """
        Resuelve y retorna el UUID del estudiante desde cualquiera
        de los tres criterios de búsqueda, en orden de prioridad:
          1. estudiante_id (UUID directo)
          2. cedula        (número de identificación exacto)
          3. nombre        (búsqueda parcial en primer_nombre o primer_apellido)

        Args:
            estudiante_id (str): UUID del estudiante. Prioridad 1.
            cedula (str):        Número de cédula exacto. Prioridad 2.
            nombre (str):        Nombre o apellido parcial. Prioridad 3.

        Returns:
            str: UUID del estudiante encontrado.

        Raises:
            ValueError: Si no se encuentra ningún estudiante o hay ambigüedad.
        """
        from estudiantes.models import Persona

        # Prioridad 1: UUID directo
        if estudiante_id:
            from estudiantes.models import Estudiante as Est
            if Est.objects.filter(pk=estudiante_id, estado='ACTIVO').exists():
                return estudiante_id
            raise ValueError(
                f'No se encontró ningún estudiante activo con ID "{estudiante_id}".'
            )

        # Prioridad 2: Cédula exacta
        if cedula:
            persona = Persona.objects.filter(
                numero_identificacion=cedula.strip(),
                activo=True
            ).first()
            if not persona:
                raise ValueError(
                    f'No se encontró ninguna persona con cédula "{cedula}".'
                )
            # Obtener estudiante vinculado a esa persona
            from estudiantes.models import Estudiante as Est
            est = Est.objects.filter(
                id_persona=persona, estado='ACTIVO'
            ).first()
            if not est:
                raise ValueError(
                    f'La persona con cédula "{cedula}" no tiene un estudiante activo vinculado.'
                )
            return str(est.id)

        # Prioridad 3: Nombre parcial
        if nombre:
            termino = nombre.strip()
            personas = Persona.objects.filter(
                activo=True
            ).filter(
                # Búsqueda en primer_nombre, segundo_nombre, primer_apellido, segundo_apellido
                **{}
            )
            # Usar icontains para búsqueda case-insensitive
            from django.db.models import Q
            personas = Persona.objects.filter(
                activo=True
            ).filter(
                Q(primer_nombre__icontains=termino)  |
                Q(segundo_nombre__icontains=termino) |
                Q(primer_apellido__icontains=termino)|
                Q(segundo_apellido__icontains=termino)
            )

            if not personas.exists():
                raise ValueError(
                    f'No se encontró ninguna persona con nombre "{nombre}".'
                )

            from estudiantes.models import Estudiante as Est
            estudiantes = Est.objects.filter(
                id_persona__in=personas, estado='ACTIVO'
            ).select_related('id_persona')

            if not estudiantes.exists():
                raise ValueError(
                    f'No se encontró ningún estudiante activo con nombre "{nombre}".'
                )

            if estudiantes.count() > 1:
                # Mostrar opciones para que el usuario sea más específico
                opciones = [
                    f'{e.nombre_completo} (cédula: {e.cedula})'
                    for e in estudiantes[:5]
                ]
                raise ValueError(
                    f'Se encontraron {estudiantes.count()} estudiantes con nombre "{nombre}". '
                    f'Sea más específico o use la cédula. '
                    f'Resultados: {" | ".join(opciones)}'
                )

            return str(estudiantes.first().id)

        raise ValueError(
            'Debe proporcionar al menos un criterio: estudiante_id, cedula o nombre.'
        )

    # ----------------------------------------------------------
    # EXPLICAR ESTUDIANTE INDIVIDUAL (endpoint dedicado)
    # ----------------------------------------------------------

    def explicar_estudiante(self, estudiante_id: str, periodo_codigo: str) -> dict:
        """
        Genera la explicación SHAP completa para un estudiante específico.
        Primero busca en ia.log_prediccion (si ya se generó el ranking),
        si no encuentra, regenera el ranking para calcular SHAP.

        Args:
            estudiante_id (str): UUID del estudiante.
            periodo_codigo (str): Código del período.

        Returns:
            dict con explicación SHAP completa para respaldo legal.
        """
        from django.db import connection as conn

        # Buscar explicación SHAP ya guardada en ia.log_prediccion
        try:
            log = LogPrediccion.objects.filter(
                entidad_tipo='estudiante',
                entidad_id=estudiante_id,
                id_modelo__nombre=self.NOMBRE_MODELO,
                id_modelo__version=self.VERSION_MODELO,
            ).order_by('-creado_en').first()

            if log and log.output_data and 'shap' in log.output_data:
                shap_guardado = log.output_data['shap']
                try:
                    est    = Estudiante.objects.select_related('id_persona').get(pk=estudiante_id)
                    nombre = est.nombre_completo
                    cedula = est.cedula
                except Exception:
                    nombre = 'No disponible'
                    cedula = 'No disponible'
                return {
                    'estudiante_id':    estudiante_id,
                    'nombre_completo':  nombre,
                    'cedula':           cedula,
                    'periodo':          periodo_codigo,
                    'puntaje_xgboost':  log.output_data.get('puntaje_xgboost'),
                    'posicion':         log.output_data.get('posicion'),
                    'fuente':           'ia.log_prediccion',
                    'generado_en':      log.creado_en.isoformat(),
                    'explicacion_shap': shap_guardado,
                    'resumen_legal':    self._generar_resumen_legal(
                        estudiante_id, log.output_data, shap_guardado
                    ),
                }
        except Exception:
            pass

        # Si no hay log guardado, regenerar el ranking
        ranking = self.generar_ranking(periodo_codigo)
        entrada = next(
            (r for r in ranking if r['estudiante_id'] == estudiante_id), None
        )
        if not entrada:
            raise ValueError(
                f'El estudiante {estudiante_id} no está en el ranking habilitado '
                f'para el período {periodo_codigo}.'
            )

        return {
            'estudiante_id':    estudiante_id,
            'nombre_completo':  entrada['nombre_completo'],
            'cedula':           entrada['cedula'],
            'periodo':          periodo_codigo,
            'puntaje_xgboost':  entrada['puntaje_xgboost'],
            'posicion':         entrada['posicion'],
            'fuente':           'ranking_generado',
            'explicacion_shap': entrada['explicacion_shap'],
            'resumen_legal':    self._generar_resumen_legal(
                estudiante_id,
                {'puntaje_xgboost': entrada['puntaje_xgboost'], 'posicion': entrada['posicion']},
                entrada['explicacion_shap']
            ),
        }

    @staticmethod
    def _generar_resumen_legal(estudiante_id: str, output: dict, shap: dict) -> dict:
        """
        Genera un resumen en lenguaje claro para uso en apelaciones
        y documentación legal institucional.

        Returns:
            dict con texto explicativo listo para incluir en actas.
        """
        contribs  = shap.get('contribuciones_por_variable', {})
        principal = shap.get('variable_mas_influyente', 'desconocida')
        posicion  = output.get('posicion', '?')
        puntaje   = output.get('puntaje_xgboost', 0)

        # Construir listado de factores para el texto legal
        factores = []
        for var, val in contribs.items():
            if abs(val) > 0.001:
                signo  = 'aumentó' if val > 0 else 'redujo'
                nombre = var.replace('_', ' ').title()
                factores.append(f'{nombre} {signo} el puntaje en {abs(val):.4f} puntos')

        return {
            'posicion_ranking':    posicion,
            'puntaje_obtenido':    puntaje,
            'factor_determinante': principal.replace('_', ' ').title(),
            'factores_detallados': factores,
            'texto_acta': (
                f'El estudiante obtuvo la posición #{posicion} en el ranking con un puntaje de '
                f'{puntaje} sobre 10. El factor más determinante fue '
                f'"{principal.replace("_", " ").title()}". '
                f'Desglose de contribuciones por variable: '
                f'{"; ".join(factores[:3])}.'
                if factores else
                f'El estudiante obtuvo la posición #{posicion} con puntaje {puntaje}.'
            ),
        }

    # ----------------------------------------------------------
    # PERSISTIR RANKING
    # ----------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def persistir_ranking(ranking: list, periodo_codigo: str):
        """
        Guarda el ranking en practicas.ranking_internado.
        Elimina primero las asignaciones y ranking anterior del período
        para evitar violaciones de FK.
        """
        periodo = Periodo.objects.filter(codigo=periodo_codigo).first()
        if not periodo:
            raise ValueError(
                f'No se encontró el período "{periodo_codigo}" en academico.periodo.'
            )

        # Eliminar asignaciones previas primero (FK → ranking)
        rankings_anteriores = RankingInternado.objects.filter(id_periodo=periodo)
        AsignacionInternado.objects.filter(
            id_ranking__in=rankings_anteriores
        ).delete()
        rankings_anteriores.delete()

        for entrada in ranking:
            estudiante = Estudiante.objects.get(pk=entrada['estudiante_id'])
            RankingInternado.objects.create(
                id_estudiante   = estudiante,
                id_periodo      = periodo,
                id_carrera      = estudiante.id_carrera,
                puntaje_total   = entrada['puntaje_xgboost'],
                detalle_puntaje = {
                    **entrada['detalle_puntaje'],
                    'shap': entrada.get('explicacion_shap'),  # ← SHAP en JSONB
                },
                posicion        = entrada['posicion'],
                habilitado      = True,
                generado_por_ia = True,
            )

    # ----------------------------------------------------------
    # ASIGNAR PLAZAS
    # ----------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def asignar_plazas(ranking: list, periodo_codigo: str) -> dict:
        """
        Asigna plazas de practicas.plaza_practica en orden de prioridad.
        Restaura cupos antes de reasignar para permitir ejecuciones repetidas.
        """
        periodo = Periodo.objects.filter(codigo=periodo_codigo).first()
        if not periodo:
            raise ValueError(
                f'No se encontró el período "{periodo_codigo}" en academico.periodo.'
            )

        plazas = list(PlazaPractica.objects.filter(
            activa=True,
            id_periodo=periodo,
        ).select_related('id_institucion'))

        if not plazas:
            raise ValueError(
                f'No hay plazas en practicas.plaza_practica '
                f'para el período "{periodo_codigo}".'
            )

        # Restaurar cupos y eliminar asignaciones previas
        for p in plazas:
            AsignacionInternado.objects.filter(id_plaza=p).delete()
            p.cupo_disponible = p.cupo_total
            p.save(update_fields=['cupo_disponible'])

        # Filtrar solo plazas con cupo
        plazas_con_cupo = [p for p in plazas if p.cupo_disponible > 0]

        asignados    = []
        lista_espera = []
        plaza_idx    = 0

        for entrada in ranking:
            if plaza_idx >= len(plazas_con_cupo):
                lista_espera.append({
                    'posicion_ranking': entrada['posicion'],
                    'estudiante':       entrada['nombre_completo'],
                    'cedula':           entrada['cedula'],
                    'puntaje_xgboost':  entrada['puntaje_xgboost'],
                })
                continue

            plaza      = plazas_con_cupo[plaza_idx]
            estudiante = Estudiante.objects.get(pk=entrada['estudiante_id'])

            ranking_obj, _ = RankingInternado.objects.get_or_create(
                id_estudiante = estudiante,
                id_periodo    = periodo,
                defaults={
                    'id_carrera':      estudiante.id_carrera,
                    'puntaje_total':   entrada['puntaje_xgboost'],
                    'detalle_puntaje': {
                        **entrada['detalle_puntaje'],
                        'shap': entrada.get('explicacion_shap'),
                    },
                    'posicion':        entrada['posicion'],
                    'habilitado':      True,
                    'generado_por_ia': True,
                }
            )

            asignacion = AsignacionInternado.objects.create(
                id_ranking    = ranking_obj,
                id_plaza      = plaza,
                estado        = 'ASIGNADA',
                es_automatica = True,
            )

            plaza.cupo_disponible -= 1
            plaza.save(update_fields=['cupo_disponible'])

            if plaza.cupo_disponible == 0:
                plaza_idx += 1

            asignados.append({
                'asignacion_id':    asignacion.id,
                'posicion_ranking': entrada['posicion'],
                'estudiante':       entrada['nombre_completo'],
                'cedula':           entrada['cedula'],
                'plaza':            plaza.nombre_plaza,
                'institucion':      plaza.id_institucion.nombre,
                'puntaje_xgboost':  entrada['puntaje_xgboost'],
            })

        return {
            'total_plazas':       sum(p.cupo_total for p in plazas),
            'total_asignados':    len(asignados),
            'total_lista_espera': len(lista_espera),
            'asignados':          asignados,
            'lista_espera':       lista_espera,
        }

    # ----------------------------------------------------------
    # CONSULTAR RANKING GUARDADO EN BD
    # ----------------------------------------------------------

    @staticmethod
    def consultar_ranking(periodo_codigo: str) -> list:
        """Consulta practicas.ranking_internado para un período."""
        periodo = Periodo.objects.filter(codigo=periodo_codigo).first()
        if not periodo:
            return []

        return [{
            'posicion':        r.posicion,
            'puntaje_xgboost': float(r.puntaje_total),
            'habilitado':      r.habilitado,
            'detalle_puntaje': r.detalle_puntaje,
            'estudiante': {
                'id':     str(r.id_estudiante.id),
                'cedula': r.id_estudiante.cedula,
                'nombre': r.id_estudiante.nombre_completo,
            },
            'plaza_asignada': {
                'id':          r.asignacion.id_plaza.id,
                'nombre':      r.asignacion.id_plaza.nombre_plaza,
                'institucion': r.asignacion.id_plaza.id_institucion.nombre,
                'estado':      r.asignacion.estado,
            } if hasattr(r, 'asignacion') else None,
        } for r in RankingInternado.objects.filter(
            id_periodo=periodo
        ).select_related(
            'id_estudiante__id_persona',
            'asignacion__id_plaza__id_institucion',
        ).order_by('posicion')]