# ============================================================
# BUSINESS.PY — App Ranking (Capa 4: Lógica de Negocio + IA)
# Algoritmo XGBoost para calcular el ranking de estudiantes.
# Validado con: xgboost==2.1.3, scikit-learn==1.6.1, Python 3.13
# ============================================================

import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from django.db import transaction

from estudiantes.models import Estudiante
from plazas.models import PlazaInternado, AsignacionPlaza


class RankingBusiness:
    """
    Lógica de negocio del ranking con XGBoost.
    El controller instancia esta clase y llama a sus métodos.
    Compatible con xgboost 2.1.3 y scikit-learn 1.6.1 (Python 3.13).
    """

    # Pesos institucionales (ajustar según reglamento)
    PESOS = {
        'calificaciones':      0.35,
        'cargas_familiares':   0.25,
        'necesidad_economica': 0.25,
        'nivel_academico':     0.10,
        'ubicacion_rural':     0.05,
    }

    PARAMETROS_MODELO = {
        'n_estimators':  100,
        'learning_rate': 0.1,
        'max_depth':     4,
        'subsample':     0.8,
        'random_state':  42,
        'verbosity':     0,
    }

    def __init__(self):
        self.modelo           = XGBRegressor(**self.PARAMETROS_MODELO)
        self.enc_estado       = LabelEncoder()
        self.enc_ubicacion    = LabelEncoder()
        self.modelo_entrenado = False

    def _preparar_df(self, qs):
        """Convierte el QuerySet de estudiantes a DataFrame de pandas."""
        return pd.DataFrame([{
            'id':                  e.id,
            'estado_civil':        e.estado_civil,
            'cargas_familiares':   int(e.cargas_familiares),
            'ubicacion':           e.ubicacion_geografica,
            'situacion_economica': int(e.situacion_economica),
            'calificaciones':      float(e.calificaciones),
            'nivel_academico':     int(e.nivel_academico),
        } for e in qs])

    def _codificar(self, df):
        """Codifica variables categóricas a numéricas para XGBoost."""
        df = df.copy()
        df['estado_civil_cod']    = self.enc_estado.fit_transform(df['estado_civil'])
        df['ubicacion_cod']       = self.enc_ubicacion.fit_transform(df['ubicacion'])
        df['es_rural']            = (df['ubicacion'] == 'rural').astype(int)
        df['necesidad_economica'] = 6 - df['situacion_economica']
        return df

    def _puntaje_base(self, df):
        """
        Calcula puntaje ponderado con los pesos institucionales.
        Normaliza cada variable a 0-1 antes de ponderar.
        Retorna valores en escala 0-10.
        """
        cal = df['calificaciones'] / 10.0
        car = df['cargas_familiares'] / df['cargas_familiares'].max().clip(1)
        nec = df['necesidad_economica'] / 5.0
        niv = df['nivel_academico'] / df['nivel_academico'].max().clip(1)
        rur = df['es_rural'].astype(float)
        return (
            cal * self.PESOS['calificaciones']      +
            car * self.PESOS['cargas_familiares']   +
            nec * self.PESOS['necesidad_economica'] +
            niv * self.PESOS['nivel_academico']     +
            rur * self.PESOS['ubicacion_rural']
        ) * 10

    def _variables_entrada(self, df):
        """Retorna solo las columnas de entrada del modelo XGBoost."""
        return df[[
            'estado_civil_cod', 'cargas_familiares', 'ubicacion_cod',
            'situacion_economica', 'calificaciones', 'nivel_academico',
            'es_rural', 'necesidad_economica',
        ]]

    def generar_ranking(self) -> list:
        """
        Ejecuta XGBoost y retorna el ranking completo de estudiantes habilitados.

        Returns:
            list: Lista ordenada de dicts con posición, datos y puntaje.

        Raises:
            ValueError: Si no hay al menos 2 estudiantes habilitados.
        """
        qs    = Estudiante.objects.filter(
            modulos_ingles_aprobados=True,
            calificaciones_cerradas=True,
        )
        total = qs.count()
        if total < 2:
            raise ValueError(
                f'Se necesitan al menos 2 estudiantes habilitados. '
                f'Actualmente hay {total}.'
            )

        df                   = self._preparar_df(qs)
        df                   = self._codificar(df)
        df['puntaje_base']   = self._puntaje_base(df)
        X, y                 = self._variables_entrada(df), df['puntaje_base']

        self.modelo.fit(X, y)
        self.modelo_entrenado    = True
        df['puntaje_xgboost']    = self.modelo.predict(X)

        df       = df.sort_values('puntaje_xgboost', ascending=False).reset_index(drop=True)
        df['posicion'] = df.index + 1

        est_dict = {e.id: e for e in qs}
        return [{
            'posicion':            int(r['posicion']),
            'estudiante_id':       int(r['id']),
            'nombre_completo':     est_dict[int(r['id'])].nombre_completo,
            'cedula':              est_dict[int(r['id'])].cedula,
            'calificaciones':      float(r['calificaciones']),
            'cargas_familiares':   int(r['cargas_familiares']),
            'situacion_economica': int(r['situacion_economica']),
            'ubicacion':           r['ubicacion'],
            'nivel_academico':     int(r['nivel_academico']),
            'puntaje_xgboost':     round(float(r['puntaje_xgboost']), 4),
            'puntaje_base':        round(float(r['puntaje_base']), 4),
        } for _, r in df.iterrows()]

    def importancia_variables(self) -> dict:
        """
        Retorna la importancia de cada variable según XGBoost.
        Útil para explicar el ranking ante apelaciones.
        """
        if not self.modelo_entrenado:
            raise ValueError('Ejecute generar_ranking() primero.')
        nombres = [
            'Estado Civil', 'Cargas Familiares', 'Ubicación Geográfica',
            'Situación Económica', 'Calificaciones', 'Nivel Académico',
            'Es Zona Rural', 'Necesidad Económica',
        ]
        return {
            n: round(float(i) * 100, 2)
            for n, i in zip(nombres, self.modelo.feature_importances_)
        }

    @staticmethod
    @transaction.atomic
    def asignar_plazas(ranking: list, periodo: str) -> dict:
        """
        Asigna plazas disponibles del período a los primeros del ranking.
        @transaction.atomic: si algo falla, revierte TODO.

        Raises:
            ValueError: Si no hay plazas disponibles en el período.
        """
        plazas = list(PlazaInternado.objects.filter(
            status=True, estado='disponible', periodo=periodo,
        ))
        if not plazas:
            raise ValueError(
                f'No hay plazas disponibles para el período "{periodo}".'
            )

        asignados, lista_espera = [], []

        for entrada in ranking:
            posicion = entrada['posicion']
            puntaje  = entrada['puntaje_xgboost']

            if posicion <= len(plazas):
                plaza      = plazas[posicion - 1]
                estudiante = Estudiante.objects.get(pk=entrada['estudiante_id'])

                asignacion = AsignacionPlaza(
                    estudiante=estudiante, plaza=plaza,
                    posicion_ranking=posicion, puntaje_xgboost=puntaje,
                    estado='asignada',
                )
                asignacion.save()   # ModelBase registra auditoría automáticamente

                plaza.estado = 'ocupada'
                plaza.save()

                asignados.append({
                    'asignacion_id':    asignacion.id,
                    'posicion_ranking': posicion,
                    'estudiante':       entrada['nombre_completo'],
                    'cedula':           entrada['cedula'],
                    'plaza_codigo':     plaza.codigo,
                    'institucion':      plaza.institucion,
                    'area':             plaza.area,
                    'puntaje_xgboost':  puntaje,
                })
            else:
                lista_espera.append({
                    'posicion_ranking': posicion,
                    'estudiante':       entrada['nombre_completo'],
                    'cedula':           entrada['cedula'],
                    'puntaje_xgboost':  puntaje,
                })

        return {
            'total_plazas':       len(plazas),
            'total_asignados':    len(asignados),
            'total_lista_espera': len(lista_espera),
            'asignados':          asignados,
            'lista_espera':       lista_espera,
        }

    @staticmethod
    def consultar_asignaciones(periodo: str) -> list:
        """Consulta asignaciones guardadas en BD para un período."""
        return [{
            'asignacion_id':    a.id,
            'posicion_ranking': a.posicion_ranking,
            'puntaje_xgboost':  float(a.puntaje_xgboost),
            'estado':           a.estado,
            'estudiante': {
                'id':             a.estudiante.id,
                'cedula':         a.estudiante.cedula,
                'nombre':         a.estudiante.nombre_completo,
                'calificaciones': float(a.estudiante.calificaciones),
            },
            'plaza': {
                'id':          a.plaza.id,
                'codigo':      a.plaza.codigo,
                'institucion': a.plaza.institucion,
                'area':        a.plaza.area,
                'ciudad':      a.plaza.ciudad,
            },
            'fecha_asignacion': a.date_create,
        } for a in AsignacionPlaza.objects.filter(
            status=True, plaza__periodo=periodo,
        ).select_related('estudiante', 'plaza').order_by('posicion_ranking')]
