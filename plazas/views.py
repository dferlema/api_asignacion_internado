# ============================================================
# VIEWS.PY — App Plazas (Capa 2: HTTP / Validación)
# Recibe request, valida con Form y delega al Controller.
# ============================================================

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from helpers.base_views import VistaAutenticada
from helpers.response_helper import respuesta_error_validacion
from .forms import PlazaInternadoForm, ActualizarEstadoPlazaForm
from .controllers import PlazasController


class PlazasListaCrearView(VistaAutenticada):
    """
    GET  /api/v1/plazas/  → Lista todas las plazas activas
    POST /api/v1/plazas/  → Crea una nueva plaza
    """

    @extend_schema(summary='Listar todas las plazas de internado activas')
    def get(self, request):
        return PlazasController.listar()

    @extend_schema(summary='Crear nueva plaza de internado')
    def post(self, request):
        form = PlazaInternadoForm(request.data)
        if not form.is_valid():
            return respuesta_error_validacion(
                mensaje='Los datos de la plaza no son válidos.',
                errores=form.errors
            )
        return PlazasController.crear(form.cleaned_data)


class PlazasDetalleView(VistaAutenticada):
    """
    GET    /api/v1/plazas/{id}/  → Ver detalle
    PUT    /api/v1/plazas/{id}/  → Actualizar completo
    DELETE /api/v1/plazas/{id}/  → Soft Delete
    """

    @extend_schema(summary='Ver detalle de una plaza')
    def get(self, request, pk):
        return PlazasController.detalle(pk)

    @extend_schema(summary='Actualizar plaza de internado')
    def put(self, request, pk):
        form = PlazaInternadoForm(request.data)
        if not form.is_valid():
            return respuesta_error_validacion(
                mensaje='Los datos de la plaza no son válidos.',
                errores=form.errors
            )
        return PlazasController.actualizar(pk, form.cleaned_data)

    @extend_schema(summary='Eliminar plaza (soft delete)')
    def delete(self, request, pk):
        return PlazasController.eliminar(pk)


class PlazasDisponiblesView(VistaAutenticada):
    """
    GET /api/v1/plazas/disponibles/?periodo=2024-1
    Lista solo las plazas con estado 'disponible'.
    """

    @extend_schema(
        summary='Listar plazas disponibles',
        parameters=[
            OpenApiParameter(
                name='periodo', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Filtrar por período (ej: 2024-1). Opcional.',
            ),
        ],
    )
    def get(self, request):
        periodo = request.query_params.get('periodo', None)
        return PlazasController.disponibles(periodo)


class AsignacionesListaView(VistaAutenticada):
    """
    GET /api/v1/plazas/asignaciones/?periodo=2024-1
    Lista todas las asignaciones registradas en el sistema.
    """

    @extend_schema(
        summary='Listar todas las asignaciones de plazas',
        parameters=[
            OpenApiParameter(
                name='periodo', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Filtrar por período académico. Opcional.',
            ),
        ],
    )
    def get(self, request):
        periodo = request.query_params.get('periodo', None)
        return PlazasController.listar_asignaciones(periodo)
