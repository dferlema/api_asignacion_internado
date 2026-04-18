# ============================================================
# VIEWS.PY — App Ranking (Capa 2: HTTP / Validación)
# ExplicarShapView acepta búsqueda por UUID, cédula o nombre.
# ============================================================

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from helpers.base_views import VistaAutenticada
from helpers.response_helper import respuesta_error_validacion
from .forms import AsignarPlazasForm, ConsultarRankingForm
from .controllers import RankingController


class GenerarRankingView(VistaAutenticada):
    """GET /api/v1/ranking/generar/ — Ejecuta XGBoost + SHAP."""

    @extend_schema(
        summary='Generar ranking automático con XGBoost + SHAP',
        description=(
            'Ejecuta XGBoost sobre los estudiantes habilitados. '
            'Cada entrada incluye explicacion_shap por variable. '
            'Registra logs en ia.log_prediccion.'
        ),
    )
    def get(self, request):
        return RankingController.generar()


class AsignarPlazasView(VistaAutenticada):
    """POST /api/v1/ranking/asignar/ — Asigna plazas con SHAP persistido."""

    @extend_schema(
        summary='Asignar plazas según ranking XGBoost + SHAP',
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
    """GET /api/v1/ranking/consultar/?periodo=2024-1"""

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


class ExplicarShapView(VistaAutenticada):
    """
    GET /api/v1/ranking/explicar/?periodo=2024-1&cedula=1700000023
    GET /api/v1/ranking/explicar/?periodo=2024-1&estudiante_id={uuid}
    GET /api/v1/ranking/explicar/?periodo=2024-1&nombre=David

    Genera la explicación SHAP para un estudiante.
    Acepta búsqueda por UUID, cédula o nombre (en ese orden de prioridad).
    Al menos uno de los tres es obligatorio junto con el período.

    Uso legal: adjuntar en actas de apelación para respaldo técnico.
    """

    @extend_schema(
        summary='Explicación SHAP — buscar por UUID, cédula o nombre',
        description=(
            'Genera la explicación SHAP completa de un estudiante. '
            'Busca por: estudiante_id (UUID), cedula (10 dígitos) o nombre (parcial). '
            'Retorna contribución de cada variable al puntaje y resumen legal. '
            'Ideal para responder apelaciones con evidencia técnica.'
        ),
        parameters=[
            OpenApiParameter(
                name='periodo', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=True,
                description='Período académico. Ejemplo: 2024-1',
            ),
            OpenApiParameter(
                name='estudiante_id', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='UUID del estudiante. Prioridad 1.',
            ),
            OpenApiParameter(
                name='cedula', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Número de cédula (10 dígitos). Prioridad 2.',
            ),
            OpenApiParameter(
                name='nombre', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Nombre o apellido (parcial). Prioridad 3.',
            ),
        ],
    )
    def get(self, request):
        # Validar período obligatorio
        periodo = request.query_params.get('periodo', '').strip()
        if not periodo:
            return respuesta_error_validacion(
                mensaje='El parámetro "periodo" es obligatorio. Ejemplo: ?periodo=2024-1'
            )

        # Obtener parámetros de búsqueda
        estudiante_id = request.query_params.get('estudiante_id', '').strip() or None
        cedula        = request.query_params.get('cedula', '').strip() or None
        nombre        = request.query_params.get('nombre', '').strip() or None

        # Validar que al menos uno de búsqueda esté presente
        if not any([estudiante_id, cedula, nombre]):
            return respuesta_error_validacion(
                mensaje=(
                    'Debe proporcionar al menos un criterio de búsqueda: '
                    '"estudiante_id" (UUID), "cedula" o "nombre".'
                )
            )

        return RankingController.explicar(
            periodo=periodo,
            estudiante_id=estudiante_id,
            cedula=cedula,
            nombre=nombre,
        )