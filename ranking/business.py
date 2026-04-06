# ============================================================
# BUSINESS.PY — App Ranking (Capa 4: Lógica de Negocio + IA)
# Lee desde tablas Innotech directamente (managed=False).
# Escribe en practicas.ranking_internado, asignacion_internado
# e ia.log_prediccion.
#
# CORRECCIÓN: _obtener_habilitados usa id_requisito (entero FK
# real de Innotech) en lugar de tipo_requisito (campo que no
# existe en la BD). Los IDs se consultan dinámicamente desde
# practicas.requisito_habilitante.
# ============================================================

import time
import pandas as pd
from xgboost import XGBRegressor
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


class RankingBusiness:
    """
    Lógica de negocio del ranking con XGBoost.
    Lee desde estudiantil.estudiante (Innotech).
    Escribe en practicas.ranking_internado e ia.log_prediccion.
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

    # ----------------------------------------------------------
    # MÉTODO AUXILIAR: obtener IDs reales de requisitos
    # ----------------------------------------------------------

    @staticmethod
    def _obtener_ids_requisitos():
        """
        Consulta practicas.requisito_habilitante y retorna los IDs
        reales de INGLES y CALIFICACIONES.
        No usa valores hardcodeados — lee siempre desde la BD.

        Returns:
            tuple: (id_ingles, id_calificaciones)
        Raises:
            ValueError: Si no existen los requisitos en la BD.
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

        Usa id_requisito (FK entero real de Innotech) obtenido
        dinámicamente desde practicas.requisito_habilitante.
        No usa el campo tipo_requisito que no existe en la BD real.
        """
        id_ingles, id_calificaciones = self._obtener_ids_requisitos()

        # Estudiantes con inglés aprobado
        con_ingles = Estudiante.objects.filter(
            verificaciones_requisitos__id_requisito=id_ingles,
            verificaciones_requisitos__cumple=True,
        ).values('id')

        # Estudiantes con calificaciones cerradas
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
        # Invertir: EXTREMA=1 → mayor necesidad → mayor puntaje
        df['necesidad_economica'] = 5 - df['situacion_economica']
        return df

    def _puntaje_base(self, df):
        """
        Calcula puntaje ponderado con pesos institucionales.
        Normaliza cada variable a 0-1. Resultado en escala 0-10.
        """
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
        """Retorna solo las columnas de entrada del modelo XGBoost."""
        return df[[
            'cargas_familiares', 'ubicacion_cod', 'situacion_economica',
            'calificaciones', 'nivel_academico', 'es_rural', 'necesidad_economica',
        ]]

    # ----------------------------------------------------------
    # MÉTODO AUXILIAR: modelo IA
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
    # GENERAR RANKING
    # ----------------------------------------------------------

    def generar_ranking(self, periodo_codigo: str = None) -> list:
        """
        Ejecuta XGBoost sobre estudiantes habilitados de Innotech.
        Lee desde estudiantil.estudiante + tablas relacionadas.
        Registra cada predicción en ia.log_prediccion.

        Args:
            periodo_codigo (str): Código del período (ej: '2024-1'). Opcional.

        Returns:
            list: Ranking ordenado por puntaje descendente.

        Raises:
            ValueError: Si no hay al menos 2 estudiantes habilitados.
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

        # --- Ejecutar XGBoost ---
        inicio_ms          = int(time.time() * 1000)
        df                 = self._preparar_df(qs)
        df                 = self._codificar(df)
        df['puntaje_base'] = self._puntaje_base(df)
        X                  = self._variables_entrada(df)
        y                  = df['puntaje_base']

        self.modelo.fit(X, y)
        self.modelo_entrenado = True
        df['puntaje_xgboost'] = self.modelo.predict(X)
        tiempo_ms             = int(time.time() * 1000) - inicio_ms

        df             = df.sort_values('puntaje_xgboost', ascending=False).reset_index(drop=True)
        df['posicion'] = df.index + 1

        # --- Registrar modelo IA y construir resultados ---
        self._modelo_ia = self._obtener_o_crear_modelo_ia()
        est_dict        = {str(e.id): e for e in qs}
        resultado       = []

        for _, r in df.iterrows():
            est     = est_dict[r['id']]
            puntaje = round(float(r['puntaje_xgboost']), 4)

            detalle = {
                'calificaciones':      float(r['calificaciones']),
                'cargas_familiares':   int(r['cargas_familiares']),
                'situacion_economica': int(r['situacion_economica']),
                'ubicacion':           r['ubicacion'],
                'nivel_academico':     int(r['nivel_academico']),
                'puntaje_base':        round(float(r['puntaje_base']), 4),
                'pesos_utilizados':    self.PESOS,
            }

            # Registrar en ia.log_prediccion
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
                    'puntaje_xgboost': puntaje,
                    'posicion':        int(r['posicion']),
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
            })

        return resultado

    def importancia_variables(self) -> dict:
        """Retorna la importancia de cada variable según XGBoost."""
        if not self.modelo_entrenado:
            raise ValueError('Ejecute generar_ranking() primero.')
        nombres = [
            'Cargas Familiares', 'Ubicación Geográfica', 'Situación Económica',
            'Calificaciones', 'Nivel Académico', 'Es Zona Rural', 'Necesidad Económica',
        ]
        return {
            n: round(float(i) * 100, 2)
            for n, i in zip(nombres, self.modelo.feature_importances_)
        }

    # ----------------------------------------------------------
    # PERSISTIR RANKING EN BD
    # ----------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def persistir_ranking(ranking: list, periodo_codigo: str):
        """
        Guarda el ranking en practicas.ranking_internado.
        Elimina el ranking anterior del mismo período antes de insertar.
        Obtiene el FK a academico.periodo desde el código.
        """
        periodo = Periodo.objects.filter(codigo=periodo_codigo).first()
        if not periodo:
            raise ValueError(
                f'No se encontró el período "{periodo_codigo}" en academico.periodo.'
            )

        # Eliminar ranking anterior del período
        RankingInternado.objects.filter(id_periodo=periodo).delete()

        for entrada in ranking:
            estudiante = Estudiante.objects.get(pk=entrada['estudiante_id'])
            RankingInternado.objects.create(
                id_estudiante   = estudiante,
                id_periodo      = periodo,
                id_carrera      = estudiante.id_carrera,
                puntaje_total   = entrada['puntaje_xgboost'],
                detalle_puntaje = entrada['detalle_puntaje'],
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
        Asigna plazas de practicas.plaza_practica a los estudiantes
        del ranking en orden de prioridad.
        Decrementa cupo_disponible tras cada asignación.

        @transaction.atomic garantiza que si algo falla se revierte todo.
        """
        periodo = Periodo.objects.filter(codigo=periodo_codigo).first()
        if not periodo:
            raise ValueError(
                f'No se encontró el período "{periodo_codigo}" en academico.periodo.'
            )

        plazas = list(PlazaPractica.objects.filter(
            activa=True,
            cupo_disponible__gt=0,
            id_periodo=periodo,
        ).select_related('id_institucion'))

        if not plazas:
            raise ValueError(
                f'No hay plazas disponibles en practicas.plaza_practica '
                f'para el período "{periodo_codigo}".'
            )

        asignados    = []
        lista_espera = []
        plaza_idx    = 0

        for entrada in ranking:
            if plaza_idx >= len(plazas):
                lista_espera.append({
                    'posicion_ranking': entrada['posicion'],
                    'estudiante':       entrada['nombre_completo'],
                    'cedula':           entrada['cedula'],
                    'puntaje_xgboost':  entrada['puntaje_xgboost'],
                })
                continue

            plaza      = plazas[plaza_idx]
            estudiante = Estudiante.objects.get(pk=entrada['estudiante_id'])

            # Obtener o crear entrada en ranking_internado
            ranking_obj, _ = RankingInternado.objects.get_or_create(
                id_estudiante = estudiante,
                id_periodo    = periodo,
                defaults={
                    'id_carrera':      estudiante.id_carrera,
                    'puntaje_total':   entrada['puntaje_xgboost'],
                    'detalle_puntaje': entrada['detalle_puntaje'],
                    'posicion':        entrada['posicion'],
                    'habilitado':      True,
                    'generado_por_ia': True,
                }
            )

            # Crear la asignación en practicas.asignacion_internado
            asignacion = AsignacionInternado.objects.create(
                id_ranking    = ranking_obj,
                id_plaza      = plaza,
                estado        = 'ASIGNADA',
                es_automatica = True,
            )

            # Decrementar cupo disponible en practicas.plaza_practica
            plaza.cupo_disponible -= 1
            plaza.save(update_fields=['cupo_disponible'])

            # Si la plaza se llenó, pasar a la siguiente
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
        """
        Consulta practicas.ranking_internado para un período.
        Retorna el ranking completo con la asignación si existe.
        """
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