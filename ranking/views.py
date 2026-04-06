# ============================================================
# VIEWS.PY — App Ranking (Capa 2: HTTP / Validación)
# Recibe request, valida con Form y delega al Controller.
# Compatible con Innotech BD.
# ============================================================

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from helpers.base_views import VistaAutenticada
from helpers.response_helper import respuesta_error_validacion
from .forms import AsignarPlazasForm, ConsultarRankingForm
from .controllers import RankingController


class GenerarRankingView(VistaAutenticada):
    """
    GET /api/v1/ranking/generar/
    Ejecuta XGBoost y retorna el ranking.
    Registra logs en ia.log_prediccion pero no persiste el ranking.
    """

    @extend_schema(
        summary='Generar ranking automático con XGBoost',
        description=(
            'Ejecuta XGBoost sobre los estudiantes habilitados y retorna '
            'el ranking ordenado por puntaje. Registra logs en ia.log_prediccion. '
            'Para persistir el ranking usar POST /asignar/.'
        ),
    )
    def get(self, request):
        return RankingController.generar()


class AsignarPlazasView(VistaAutenticada):
    """
    POST /api/v1/ranking/asignar/
    Genera ranking, lo persiste en practicas.ranking_internado
    y asigna plazas disponibles del período.

    Body JSON requerido:
    {
        "periodo": "2024-1"
    }
    """

    @extend_schema(
        summary='Asignar plazas de internado según ranking XGBoost',
        description=(
            'Genera el ranking con XGBoost, lo persiste en ranking_internado '
            'y asigna automáticamente las plazas disponibles del período. '
            'Toda la operación es transaccional.'
        ),
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'periodo': {'type': 'string', 'example': '2024-1'},
                },
                'required': ['periodo'],
            }
        },
    )
    def post(self, request):
        form = AsignarPlazasForm(request.data)
        if not form.is_valid():
            return respuesta_error_validacion(
                mensaje='Los datos de entrada no son válidos.',
                errores=form.errors
            )
        return RankingController.asignar(form.cleaned_data['periodo'])


class ConsultarRankingView(VistaAutenticada):
    """
    GET /api/v1/ranking/consultar/?periodo=2024-1
    Consulta el ranking y asignaciones ya persistidos en BD.
    """

    @extend_schema(
        summary='Consultar ranking y asignaciones guardadas',
        parameters=[
            OpenApiParameter(
                name='periodo', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=True,
                description='Período a consultar. Ejemplo: 2024-1',
            ),
        ],
    )
    def get(self, request):
        form = ConsultarRankingForm(request.query_params)
        if not form.is_valid():
            return respuesta_error_validacion(
                mensaje='El parámetro de consulta no es válido.',
                errores=form.errors
            )
        return RankingController.consultar(form.cleaned_data['periodo'])