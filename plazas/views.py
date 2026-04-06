from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from helpers.base_views import VistaAutenticada
from helpers.response_helper import respuesta_error_validacion
from .forms import PlazaPracticaForm
from .controllers import PlazasController


class PlazasListaCrearView(VistaAutenticada):
    @extend_schema(summary='Listar todas las plazas activas')
    def get(self, request):
        return PlazasController.listar()

    @extend_schema(summary='Crear nueva plaza')
    def post(self, request):
        form = PlazaPracticaForm(request.data)
        if not form.is_valid():
            return respuesta_error_validacion(
                mensaje='Los datos de la plaza no son válidos.',
                errores=form.errors
            )
        return PlazasController.crear(form.cleaned_data)


class PlazasDetalleView(VistaAutenticada):
    @extend_schema(summary='Ver detalle de una plaza')
    def get(self, request, pk):
        return PlazasController.detalle(pk)

    @extend_schema(summary='Actualizar plaza')
    def put(self, request, pk):
        form = PlazaPracticaForm(request.data)
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
    @extend_schema(
        summary='Listar plazas con cupo disponible',
        parameters=[
            OpenApiParameter(
                name='periodo', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Filtrar por período (ej: 2024-1).',
            ),
        ],
    )
    def get(self, request):
        return PlazasController.disponibles(request.query_params.get('periodo'))


class AsignacionesListaView(VistaAutenticada):
    @extend_schema(
        summary='Listar todas las asignaciones',
        parameters=[
            OpenApiParameter(
                name='periodo', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
            ),
        ],
    )
    def get(self, request):
        return PlazasController.listar_asignaciones(request.query_params.get('periodo'))