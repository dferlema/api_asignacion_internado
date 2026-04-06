from django.urls import path
from .views import (
    PlazasListaCrearView,
    PlazasDetalleView,
    PlazasDisponiblesView,
    AsignacionesListaView,
)

urlpatterns = [
    path('', PlazasListaCrearView.as_view(), name='plazas-lista'),
    path('disponibles/', PlazasDisponiblesView.as_view(), name='plazas-disponibles'),
    path('asignaciones/', AsignacionesListaView.as_view(), name='plazas-asignaciones'),
    path('<int:pk>/', PlazasDetalleView.as_view(), name='plazas-detalle'),
]