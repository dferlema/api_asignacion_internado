# ============================================================
# URLS.PY — App Estudiantes (Capa 1: Enrutamiento)
# Solo rutas de consulta — los datos vienen del ERP Innotech.
# pk es UUID (str).
# ============================================================

from django.urls import path
from .views import (
    EstudiantesListaView,
    EstudiantesDetalleView,
    EstudiantesHabilitadosView,
    EstudiantesValidarRequisitosView,
)

urlpatterns = [
    # Lista completa de estudiantes activos
    path('', EstudiantesListaView.as_view(), name='estudiantes-lista'),

    # Endpoints especiales ANTES del detalle para evitar conflictos
    path('habilitados/', EstudiantesHabilitadosView.as_view(), name='estudiantes-habilitados'),

    # Detalle por UUID
    path('<str:pk>/', EstudiantesDetalleView.as_view(), name='estudiantes-detalle'),
    path('<str:pk>/validar-requisitos/', EstudiantesValidarRequisitosView.as_view(), name='estudiantes-validar'),
]

# Rutas disponibles:
# GET /api/v1/estudiantes/                          → Listar activos
# GET /api/v1/estudiantes/habilitados/              → Solo habilitados
# GET /api/v1/estudiantes/{uuid}/                   → Detalle
# GET /api/v1/estudiantes/{uuid}/validar-requisitos/ → Validar requisitos