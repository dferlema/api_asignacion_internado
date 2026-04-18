# ============================================================
# URLS.PY — App Ranking (Capa 1: Enrutamiento)
# El endpoint SHAP ahora usa query params en lugar de UUID en URL.
# ============================================================

from django.urls import path
from .views import (
    GenerarRankingView,
    AsignarPlazasView,
    ConsultarRankingView,
    ExplicarShapView,
)

urlpatterns = [
    path('generar/',   GenerarRankingView.as_view(),  name='ranking-generar'),
    path('asignar/',   AsignarPlazasView.as_view(),   name='ranking-asignar'),
    path('consultar/', ConsultarRankingView.as_view(), name='ranking-consultar'),
    path('explicar/',  ExplicarShapView.as_view(),    name='ranking-explicar'),
]

# Rutas disponibles:
# GET  /api/v1/ranking/generar/                                        → Ranking + SHAP
# POST /api/v1/ranking/asignar/                                        → Asignar plazas
# GET  /api/v1/ranking/consultar/?periodo=X                            → Consultar BD
# GET  /api/v1/ranking/explicar/?periodo=X&cedula=XXXXXXXXXX           → SHAP por cédula
# GET  /api/v1/ranking/explicar/?periodo=X&estudiante_id={uuid}        → SHAP por UUID
# GET  /api/v1/ranking/explicar/?periodo=X&nombre=Juan                 → SHAP por nombre