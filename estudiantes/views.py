# ============================================================
# VIEWS.PY — App Estudiantes (Capa 2: HTTP)
# managed=False: el API solo consulta datos de Innotech.
# No hay POST/PUT/DELETE de estudiante — los datos personales
# se gestionan desde el ERP Innotech (core.persona).
# El sistema solo gestiona: estado, requisitos y ranking.
# ============================================================

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from helpers.base_views import VistaAutenticada
from .controllers import EstudiantesController


class EstudiantesListaView(VistaAutenticada):
    """GET /api/v1/estudiantes/ — Lista estudiantes activos de Innotech."""

    @extend_schema(
        summary='Listar estudiantes activos',
        description='Lee desde estudiantil.estudiante. Solo retorna estado=ACTIVO.'
    )
    def get(self, request):
        return EstudiantesController.listar()


class EstudiantesDetalleView(VistaAutenticada):
    """GET /api/v1/estudiantes/{uuid}/ — Detalle de un estudiante."""

    @extend_schema(summary='Ver detalle de un estudiante')
    def get(self, request, pk):
        return EstudiantesController.detalle(pk)


class EstudiantesHabilitadosView(VistaAutenticada):
    """GET /api/v1/estudiantes/habilitados/ — Solo habilitados para internado."""

    @extend_schema(
        summary='Listar estudiantes habilitados para internado',
        description=(
            'Retorna estudiantes con inglés aprobado Y calificaciones cerradas '
            'según practicas.verificacion_requisito.'
        )
    )
    def get(self, request):
        return EstudiantesController.habilitados()


class EstudiantesValidarRequisitosView(VistaAutenticada):
    """GET /api/v1/estudiantes/{uuid}/validar-requisitos/"""

    @extend_schema(
        summary='Validar requisitos habilitantes de un estudiante',
        description='Consulta practicas.verificacion_requisito y retorna detalle.'
    )
    def get(self, request, pk):
        return EstudiantesController.validar_requisitos(pk)