"""
=============================================================
GENERAR_METRICAS.PY — Sistema 17 / internado_api
=============================================================
Propósito:
    Ejecuta el pipeline XGBoost sobre los datos reales de
    innotech_db y genera todas las métricas necesarias para
    el Capítulo III del trabajo de titulación UBE.

Métricas generadas:
    - MAE   (Error Absoluto Medio)
    - RMSE  (Raíz del Error Cuadrático Medio)
    - R²    (Coeficiente de Determinación)
    - Importancia de variables (feature importance)
    - Valores SHAP por variable
    - Tiempo de ejecución del pipeline
    - Estadísticas descriptivas del ranking generado

Uso:
    Desde la raíz del proyecto (donde está manage.py):
    python generar_metricas.py

Requisitos:
    - La base de datos innotech_db debe estar corriendo (Docker)
    - generar_datos.py debe haberse ejecutado antes
    - Las variables de entorno en .env deben estar configuradas
=============================================================
"""

import os
import sys
import time
import json
import django

# ── Configurar Django antes de importar cualquier modelo ──
# Agrega la raíz del proyecto al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'internado.settings')
django.setup()

# ── Importaciones del proyecto (después de django.setup()) ──
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ranking.business import RankingBusiness


# =============================================================
# FUNCIÓN PRINCIPAL
# =============================================================

def generar_metricas():
    """
    Ejecuta el pipeline completo y calcula todas las métricas
    del modelo XGBoost para documentación académica.
    """

    print("\n" + "=" * 60)
    print("  SISTEMA 17 — GENERADOR DE MÉTRICAS PARA TITULACIÓN")
    print("  Universidad Bolivariana del Ecuador")
    print("=" * 60)

    # ── Paso 1: Instanciar el business y ejecutar el pipeline ──
    print("\n[1/5] Ejecutando pipeline XGBoost sobre innotech_db...")
    inicio_total = time.time()

    rb = RankingBusiness()

    try:
        # Generar ranking con el período de prueba
        # Cambia '2024-1' si tu período tiene otro código en la BD
        ranking = rb.generar_ranking(periodo_codigo='2024-1')
    except ValueError as e:
        print(f"\n  ERROR: {e}")
        print("\n  Solución: Ejecuta primero 'python generar_datos.py'")
        sys.exit(1)

    tiempo_pipeline = round(time.time() - inicio_total, 3)
    print(f"  ✓ Pipeline ejecutado en {tiempo_pipeline} segundos")
    print(f"  ✓ Estudiantes en el ranking: {len(ranking)}")

    # ── Paso 2: Reconstruir X e y desde el business para métricas ──
    print("\n[2/5] Calculando métricas de regresión...")

    # Recuperar los datos internos del modelo ya entrenado
    # El business guarda X en self._X_entrenado después del fit()
    X = rb._X_entrenado
    y_real = rb._puntaje_base(rb._codificar(rb._preparar_df(rb._obtener_habilitados())))
    y_pred = rb.modelo.predict(X)

    # Métricas de regresión estándar para XGBRegressor
    mae  = mean_absolute_error(y_real, y_pred)
    rmse = np.sqrt(mean_squared_error(y_real, y_pred))
    r2   = r2_score(y_real, y_pred)

    print(f"  ✓ MAE  (Error Absoluto Medio):          {mae:.4f}")
    print(f"  ✓ RMSE (Raíz Error Cuadrático Medio):   {rmse:.4f}")
    print(f"  ✓ R²   (Coeficiente Determinación):     {r2:.4f}")

    # ── Paso 3: Importancia de variables ──
    print("\n[3/5] Calculando importancia de variables (feature importance)...")

    importancias = rb.importancia_variables()

    print("\n  Variable                  | Importancia (%)")
    print("  " + "-" * 45)
    for var, imp in sorted(importancias.items(), key=lambda x: x[1], reverse=True):
        barra = "█" * int(imp / 2)
        print(f"  {var:<25} | {imp:>6.2f}%  {barra}")

    # ── Paso 4: Estadísticas descriptivas del ranking ──
    print("\n[4/5] Estadísticas descriptivas del ranking generado...")

    puntajes = [r['puntaje_xgboost'] for r in ranking]
    puntajes_arr = np.array(puntajes)

    print(f"  Puntaje máximo:   {puntajes_arr.max():.4f}")
    print(f"  Puntaje mínimo:   {puntajes_arr.min():.4f}")
    print(f"  Puntaje promedio: {puntajes_arr.mean():.4f}")
    print(f"  Desv. estándar:   {puntajes_arr.std():.4f}")
    print(f"  Mediana:          {np.median(puntajes_arr):.4f}")

    # Top 5 del ranking para mostrar en el documento
    print("\n  TOP 5 del Ranking:")
    print(f"  {'Pos':<4} {'Nombre':<30} {'Cédula':<12} {'Puntaje':>8}")
    print("  " + "-" * 58)
    for r in ranking[:5]:
        nombre_corto = r['nombre_completo'][:28]
        print(
            f"  {r['posicion']:<4} "
            f"{nombre_corto:<30} "
            f"{r['cedula']:<12} "
            f"{r['puntaje_xgboost']:>8.4f}"
        )

    # ── Paso 5: Guardar resultados en JSON para el documento ──
    print("\n[5/5] Guardando resultados en 'metricas_titulacion.json'...")

    resultados = {
        "sistema": "Sistema 17 — Asignación Automatizada de Prácticas Preprofesionales",
        "universidad": "Universidad Bolivariana del Ecuador",
        "modelo": {
            "nombre": rb.NOMBRE_MODELO,
            "version": rb.VERSION_MODELO,
            "tipo": "XGBRegressor",
            "hiperparametros": rb.PARAMETROS_MODELO,
            "pesos_institucionales": rb.PESOS,
        },
        "metricas_regresion": {
            "MAE":  round(float(mae), 4),
            "RMSE": round(float(rmse), 4),
            "R2":   round(float(r2), 4),
            "interpretacion": {
                "MAE":  "El modelo se desvía en promedio este valor del puntaje real",
                "RMSE": "Penaliza más los errores grandes; indica dispersión del error",
                "R2":   "Proporción de varianza explicada por el modelo (1.0 = perfecto)",
            }
        },
        "importancia_variables": importancias,
        "estadisticas_ranking": {
            "total_estudiantes": len(ranking),
            "puntaje_maximo":    round(float(puntajes_arr.max()), 4),
            "puntaje_minimo":    round(float(puntajes_arr.min()), 4),
            "puntaje_promedio":  round(float(puntajes_arr.mean()), 4),
            "desviacion_estandar": round(float(puntajes_arr.std()), 4),
            "mediana":           round(float(np.median(puntajes_arr)), 4),
        },
        "rendimiento": {
            "tiempo_pipeline_segundos": tiempo_pipeline,
            "tiempo_pipeline_ms":       round(tiempo_pipeline * 1000),
        },
        "top_5_ranking": [
            {
                "posicion":       r['posicion'],
                "nombre":         r['nombre_completo'],
                "cedula":         r['cedula'],
                "puntaje":        r['puntaje_xgboost'],
                "calificaciones": r['calificaciones'],
                "cargas_familiares": r['cargas_familiares'],
                "situacion_economica": r['situacion_economica'],
                "ubicacion":      r['ubicacion'],
            }
            for r in ranking[:5]
        ],
        # SHAP del estudiante en posición 1 como ejemplo para el documento
        "ejemplo_shap_posicion_1": ranking[0].get('explicacion_shap') if ranking else None,
    }

    # Guardar en archivo JSON con formato legible
    with open('metricas_titulacion.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("  ✓ Archivo guardado: metricas_titulacion.json")

    # ── Resumen final ──
    print("\n" + "=" * 60)
    print("  RESUMEN PARA EL DOCUMENTO DE TITULACIÓN")
    print("=" * 60)
    print(f"\n  Modelo:          XGBRegressor v{rb.VERSION_MODELO}")
    print(f"  Estudiantes:     {len(ranking)}")
    print(f"  MAE:             {mae:.4f}")
    print(f"  RMSE:            {rmse:.4f}")
    print(f"  R²:              {r2:.4f}")
    print(f"  Tiempo ejecución: {tiempo_pipeline}s ({round(tiempo_pipeline * 1000)}ms)")
    print(f"\n  Variable más importante:")
    var_principal = max(importancias, key=importancias.get)
    print(f"  → '{var_principal}' con {importancias[var_principal]:.2f}% de importancia")
    print("\n  Archivo de métricas: metricas_titulacion.json")
    print("=" * 60 + "\n")


# =============================================================
# PUNTO DE ENTRADA
# =============================================================

if __name__ == '__main__':
    generar_metricas()
