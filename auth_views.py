# ============================================================
# AUTH_VIEWS.PY — Endpoints de autenticación
# Login y Logout con JWT almacenado en cookies HttpOnly.
# Las cookies HttpOnly no son accesibles desde JavaScript,
# protegiendo contra ataques XSS.
#
# Endpoints:
#   POST /api/v1/auth/login/   → genera tokens JWT
#   POST /api/v1/auth/logout/  → elimina tokens JWT
# ============================================================

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema

from helpers.base_views import VistaPublica, VistaAutenticada
from helpers.response_helper import (
    respuesta_exito,
    respuesta_error_general,
    respuesta_error_validacion,
)
from helpers.auth_helper import (
    generar_tokens_para_usuario,
    establecer_cookies_jwt,
    eliminar_cookies_jwt,
    verificar_rate_limit,
    registrar_intento_fallido,
    limpiar_intentos_fallidos,
)


class LoginView(VistaPublica):
    """
    POST /api/v1/auth/login/
    Autentica al usuario y genera tokens JWT almacenados
    en cookies HttpOnly (no accesibles desde JavaScript).

    Body JSON requerido:
    {
        "username": "admin",
        "password": "tu_password"
    }

    Respuesta exitosa:
    {
        "success": true,
        "message": "Sesión iniciada correctamente.",
        "data": { "username": "admin", "email": "..." }
    }
    """

    @extend_schema(
        summary='Iniciar sesión',
        description=(
            'Autentica al usuario con username y password. '
            'Genera tokens JWT almacenados en cookies HttpOnly. '
            'Rate limiting: máximo 5 intentos fallidos por IP cada 5 minutos.'
        ),
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'example': 'admin'},
                    'password': {'type': 'string', 'example': 'tu_password'},
                },
                'required': ['username', 'password'],
            }
        },
    )
    def post(self, request):
        # --- Obtener IP del cliente para rate limiting ---
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR', '127.0.0.1')

        # --- Validar que vengan los campos requeridos ---
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()

        if not username or not password:
            return respuesta_error_validacion(
                mensaje='Los campos username y password son obligatorios.',
                errores={
                    'username': ['Este campo es requerido.'] if not username else [],
                    'password': ['Este campo es requerido.'] if not password else [],
                }
            )

        # --- Verificar rate limiting antes de intentar autenticar ---
        estado = verificar_rate_limit(ip)
        if estado['bloqueado']:
            minutos = estado['segundos'] // 60
            segundos = estado['segundos'] % 60
            return respuesta_error_general(
                mensaje=(
                    f'Demasiados intentos fallidos. '
                    f'Intente nuevamente en {minutos}m {segundos}s.'
                ),
                codigo=429
            )

        # --- Autenticar credenciales ---
        usuario = authenticate(
            request=request,
            username=username,
            password=password
        )

        if not usuario:
            # Registrar intento fallido para rate limiting
            registrar_intento_fallido(ip)
            intentos_restantes = 5 - (estado['intentos'] + 1)

            return respuesta_error_general(
                mensaje=(
                    f'Usuario o contraseña incorrectos. '
                    f'Intentos restantes: {max(0, intentos_restantes)}.'
                ),
                codigo=401
            )

        # --- Login exitoso ---
        limpiar_intentos_fallidos(ip)

        # Verificar que el usuario esté activo
        if not usuario.is_active:
            return respuesta_error_general(
                mensaje='Esta cuenta está desactivada. Contacte al administrador.',
                codigo=403
            )

        # Generar tokens JWT
        refresh, access = generar_tokens_para_usuario(usuario)

        # Construir respuesta con datos del usuario
        response = respuesta_exito(
            mensaje='Sesión iniciada correctamente.',
            datos={
                'id':           usuario.id,
                'username':     usuario.username,
                'email':        usuario.email,
                'nombre':       usuario.get_full_name() or usuario.username,
                'es_admin':     usuario.is_staff,
                'es_superuser': usuario.is_superuser,
            }
        )

        # Establecer tokens como cookies HttpOnly
        return establecer_cookies_jwt(response, refresh, access)


class LogoutView(VistaAutenticada):
    """
    POST /api/v1/auth/logout/
    Cierra la sesión eliminando las cookies JWT del navegador.
    No requiere body — usa el token de la cookie automáticamente.
    """

    @extend_schema(
        summary='Cerrar sesión',
        description=(
            'Elimina las cookies JWT del navegador, '
            'cerrando la sesión del usuario actual.'
        ),
    )
    def post(self, request):
        response = respuesta_exito(
            mensaje=f'Sesión cerrada correctamente. Hasta pronto, {request.user.username}.'
        )
        return eliminar_cookies_jwt(response)


class PerfilView(VistaAutenticada):
    """
    GET /api/v1/auth/perfil/
    Retorna los datos del usuario autenticado actualmente.
    Útil para que el frontend verifique si la sesión sigue activa.
    """

    @extend_schema(
        summary='Ver perfil del usuario autenticado',
        description='Retorna los datos del usuario cuyo token JWT está en la cookie.',
    )
    def get(self, request):
        usuario = request.user
        return respuesta_exito(
            mensaje='Perfil del usuario autenticado.',
            datos={
                'id':           usuario.id,
                'username':     usuario.username,
                'email':        usuario.email,
                'nombre':       usuario.get_full_name() or usuario.username,
                'es_admin':     usuario.is_staff,
                'es_superuser': usuario.is_superuser,
                'ultimo_login': usuario.last_login,
            }
        )
