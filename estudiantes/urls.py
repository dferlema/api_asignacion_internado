# ============================================================
# URLS.PY — App Estudiantes (Capa 1: Enrutamiento)
# Define qué URL ejecuta qué vista. Sin lógica aquí.
# ============================================================

from django.urls import path
from .views import (
    EstudiantesListaCrearView,
    EstudiantesDetalleView,
    EstudiantesHabilitadosView,
    EstudiantesValidarRequisitosView,
)

urlpatterns = [
    # Lista y creación
    path('', EstudiantesListaCrearView.as_view(), name='estudiantes-lista'),

    # Detalle, actualización y eliminación
    path('<int:pk>/', EstudiantesDetalleView.as_view(), name='estudiantes-detalle'),

    # Endpoints especiales
    path('habilitados/', EstudiantesHabilitadosView.as_view(), name='estudiantes-habilitados'),
    path('<int:pk>/validar-requisitos/', EstudiantesValidarRequisitosView.as_view(), name='estudiantes-validar'),
]
