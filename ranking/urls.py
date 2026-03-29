# ============================================================
# URLS.PY — App Ranking (Capa 1: Enrutamiento)
# Define las 3 rutas principales del sistema de IA.
# ============================================================

from django.urls import path
from .views import GenerarRankingView, AsignarPlazasView, ConsultarRankingView

urlpatterns = [
    # Genera ranking en memoria (sin guardar)
    path('generar/',   GenerarRankingView.as_view(),  name='ranking-generar'),

    # Genera ranking y asigna plazas en BD
    path('asignar/',   AsignarPlazasView.as_view(),   name='ranking-asignar'),

    # Consulta asignaciones ya guardadas
    path('consultar/', ConsultarRankingView.as_view(), name='ranking-consultar'),
]

# Rutas disponibles:
# GET  /api/v1/ranking/generar/              → Ver ranking (XGBoost, sin guardar)
# POST /api/v1/ranking/asignar/              → Asignar plazas y guardar en BD
# GET  /api/v1/ranking/consultar/?periodo=X  → Consultar asignaciones guardadas
