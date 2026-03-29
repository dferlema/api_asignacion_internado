# ============================================================
# VIEWS.PY — App Ranking (Capa 2: HTTP / Validación)
# Recibe request, valida con Form y delega al Controller.
# No contiene lógica de negocio ni lógica de IA.
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
    Ejecuta XGBoost y retorna el ranking. No guarda en BD.
    Solo lectura — no requiere body ni parámetros.
    """

    @extend_schema(
        summary='Generar ranking automático con XGBoost',
        description=(
            'Ejecuta el algoritmo XGBoost sobre los estudiantes habilitados '
            'y retorna el ranking ordenado por puntaje de prioridad. '
            'También incluye la importancia de cada variable para transparencia '
            'ante posibles apelaciones. No guarda datos en la base de datos.'
        ),
    )
    def get(self, request):
        # No requiere validación de entrada, delega directamente
        return RankingController.generar()


class AsignarPlazasView(VistaAutenticada):
    """
    POST /api/v1/ranking/asignar/
    Genera ranking y asigna plazas disponibles. Guarda en BD.

    Body JSON requerido:
    {
        "periodo": "2024-1"
    }
    """

    @extend_schema(
        summary='Asignar plazas de internado según ranking XGBoost',
        description=(
            'Genera el ranking con XGBoost y asigna automáticamente las plazas '
            'disponibles del período indicado. Registra cada asignación en la BD '
            'con su puntaje para auditorías y respuesta a apelaciones. '
            'Toda la operación es transaccional: si algo falla, se revierte todo.'
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
        # Capa 6 (Form): valida el período de entrada
        form = AsignarPlazasForm(request.data)
        if not form.is_valid():
            return respuesta_error_validacion(
                mensaje='Los datos de entrada no son válidos.',
                errores=form.errors
            )
        # Capa 3 (Controller): orquesta la asignación
        return RankingController.asignar(form.cleaned_data['periodo'])


class ConsultarRankingView(VistaAutenticada):
    """
    GET /api/v1/ranking/consultar/?periodo=2024-1
    Consulta asignaciones ya guardadas en BD. No ejecuta XGBoost.
    """

    @extend_schema(
        summary='Consultar asignaciones guardadas por período',
        description=(
            'Retorna las asignaciones ya registradas en la base de datos '
            'para un período específico, ordenadas por posición en el ranking. '
            'No vuelve a ejecutar el algoritmo XGBoost.'
        ),
        parameters=[
            OpenApiParameter(
                name='periodo',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Período académico a consultar. Ejemplo: 2024-1',
            ),
        ],
    )
    def get(self, request):
        # Capa 6 (Form): valida el parámetro de la query string
        form = ConsultarRankingForm(request.query_params)
        if not form.is_valid():
            return respuesta_error_validacion(
                mensaje='El parámetro de consulta no es válido.',
                errores=form.errors
            )
        # Capa 3 (Controller): orquesta la consulta
        return RankingController.consultar(form.cleaned_data['periodo'])
