# ============================================================
# VIEWS.PY — App Estudiantes (Capa 2: HTTP / Validación)
# Recibe el request HTTP, valida con el Form y delega
# TODA la lógica al Controller. No tiene lógica de negocio.
# ============================================================

from drf_spectacular.utils import extend_schema
from helpers.base_views import VistaAutenticada
from helpers.response_helper import respuesta_error_validacion
from .forms import EstudianteForm
from .controllers import EstudiantesController


class EstudiantesListaCrearView(VistaAutenticada):
    """
    GET  /api/v1/estudiantes/  → Lista todos los estudiantes
    POST /api/v1/estudiantes/  → Registra un nuevo estudiante
    """

    @extend_schema(summary='Listar todos los estudiantes activos')
    def get(self, request):
        return EstudiantesController.listar(request)

    @extend_schema(summary='Registrar nuevo estudiante')
    def post(self, request):
        # Capa 6 (Form): valida los datos de entrada
        form = EstudianteForm(request.data)
        if not form.is_valid():
            return respuesta_error_validacion(
                mensaje='Los datos ingresados no son válidos.',
                errores=form.errors
            )
        # Capa 3 (Controller): orquesta la creación
        return EstudiantesController.crear(form.cleaned_data)


class EstudiantesDetalleView(VistaAutenticada):
    """
    GET    /api/v1/estudiantes/{id}/  → Ver detalle
    PUT    /api/v1/estudiantes/{id}/  → Actualizar completo
    DELETE /api/v1/estudiantes/{id}/  → Soft Delete
    """

    @extend_schema(summary='Ver detalle de un estudiante')
    def get(self, request, pk):
        return EstudiantesController.detalle(pk)

    @extend_schema(summary='Actualizar estudiante')
    def put(self, request, pk):
        form = EstudianteForm(request.data)
        if not form.is_valid():
            return respuesta_error_validacion(
                mensaje='Los datos ingresados no son válidos.',
                errores=form.errors
            )
        return EstudiantesController.actualizar(pk, form.cleaned_data)

    @extend_schema(summary='Eliminar estudiante (soft delete)')
    def delete(self, request, pk):
        return EstudiantesController.eliminar(pk)


class EstudiantesHabilitadosView(VistaAutenticada):
    """
    GET /api/v1/estudiantes/habilitados/
    Lista solo los estudiantes que cumplen requisitos habilitantes.
    """

    @extend_schema(summary='Listar estudiantes habilitados para internado')
    def get(self, request):
        return EstudiantesController.habilitados()


class EstudiantesValidarRequisitosView(VistaAutenticada):
    """
    GET /api/v1/estudiantes/{id}/validar-requisitos/
    Valida los requisitos habilitantes de un estudiante específico.
    """

    @extend_schema(summary='Validar requisitos habilitantes de un estudiante')
    def get(self, request, pk):
        return EstudiantesController.validar_requisitos(pk)
