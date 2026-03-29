# ============================================================
# URLS.PY — App Plazas (Capa 1: Enrutamiento)
# ============================================================

from django.urls import path
from .views import (
    PlazasListaCrearView,
    PlazasDetalleView,
    PlazasDisponiblesView,
    AsignacionesListaView,
)

urlpatterns = [
    # Lista y creación de plazas
    path('', PlazasListaCrearView.as_view(), name='plazas-lista'),

    # Detalle, actualización y eliminación
    path('<int:pk>/', PlazasDetalleView.as_view(), name='plazas-detalle'),

    # Solo plazas disponibles
    path('disponibles/', PlazasDisponiblesView.as_view(), name='plazas-disponibles'),

    # Historial de asignaciones
    path('asignaciones/', AsignacionesListaView.as_view(), name='plazas-asignaciones'),
]

# Rutas disponibles:
# GET  /api/v1/plazas/                        → Listar todas las plazas
# POST /api/v1/plazas/                        → Crear nueva plaza
# GET  /api/v1/plazas/{id}/                   → Ver detalle
# PUT  /api/v1/plazas/{id}/                   → Actualizar plaza
# DEL  /api/v1/plazas/{id}/                   → Soft delete
# GET  /api/v1/plazas/disponibles/            → Solo disponibles
# GET  /api/v1/plazas/asignaciones/           → Ver asignaciones
