# ============================================================
# BASE_VIEWS.PY — Clases base para todas las vistas del sistema
# Define los 3 tipos de vista: autenticada, pública y opcional.
# Todas las vistas del proyecto deben heredar de una de estas.
# ============================================================

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication


class VistaAutenticada(APIView):
    """
    Vista base para endpoints que REQUIEREN autenticación JWT.
    El token se lee automáticamente desde la cookie HttpOnly
    'access_token'. Si no hay token válido, retorna 401.

    Uso:
        class MiVista(VistaAutenticada):
            def get(self, request):
                usuario = request.user  # Siempre disponible
                ...
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]


class VistaPublica(APIView):
    """
    Vista base para endpoints SIN autenticación requerida.
    Accesibles por cualquier usuario anónimo.

    Uso típico: login, registro público, consultas abiertas.

    Uso:
        class LoginVista(VistaPublica):
            def post(self, request):
                ...
    """
    authentication_classes = []
    permission_classes     = [AllowAny]


class VistaOpcional(APIView):
    """
    Vista base para endpoints donde la autenticación es opcional.
    Si el usuario está autenticado, request.user estará disponible.
    Si no está autenticado, request.user será AnonymousUser.

    Útil para endpoints que muestran más información a autenticados.

    Uso:
        class ConsultaVista(VistaOpcional):
            def get(self, request):
                if request.user.is_authenticated:
                    # mostrar datos adicionales
                    ...
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [AllowAny]
