# ============================================================
# AUTH_HELPER.PY — JWT con HttpOnly Cookies y Rate Limiting
# Gestiona la creación, lectura y eliminación de tokens JWT
# usando cookies HttpOnly (protección contra ataques XSS).
# Rate limiting: 5 intentos fallidos / 5 minutos por IP.
# ============================================================

from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

# --- Configuración de cookies ---
NOMBRE_COOKIE_ACCESS  = 'access_token'   # Nombre de la cookie de acceso
NOMBRE_COOKIE_REFRESH = 'refresh_token'  # Nombre de la cookie de refresco
DURACION_ACCESS       = 30              # Minutos que dura el token de acceso
DURACION_REFRESH      = 7              # Días que dura el token de refresco

# --- Configuración de rate limiting ---
MAX_INTENTOS_LOGIN    = 5              # Intentos antes de bloquear
TIEMPO_BLOQUEO_MIN    = 5              # Minutos de bloqueo tras superar el límite


def generar_tokens_para_usuario(usuario):
    """
    Genera un par de tokens JWT (access + refresh) para el usuario.

    Args:
        usuario: Instancia del modelo User de Django.

    Returns:
        tuple: (refresh_token, access_token) como strings.

    Ejemplo:
        refresh, access = generar_tokens_para_usuario(request.user)
    """
    refresh = RefreshToken.for_user(usuario)
    return refresh, refresh.access_token


def establecer_cookies_jwt(response, refresh_token, access_token):
    """
    Establece los tokens JWT como cookies HttpOnly en la respuesta.
    Las cookies HttpOnly NO son accesibles desde JavaScript,
    protegiéndolas contra ataques XSS.

    Args:
        response:      Objeto Response de DRF.
        refresh_token: Token de refresco JWT.
        access_token:  Token de acceso JWT.

    Returns:
        response con las cookies configuradas.
    """
    # Cookie del token de acceso (corta duración: 30 min)
    response.set_cookie(
        key=NOMBRE_COOKIE_ACCESS,
        value=str(access_token),
        max_age=DURACION_ACCESS * 60,    # Convertir a segundos
        httponly=True,                   # No accesible desde JS (anti-XSS)
        secure=True,                     # Solo HTTPS en producción
        samesite='Lax',                  # Protección CSRF
        path='/',
    )

    # Cookie del token de refresco (larga duración: 7 días)
    response.set_cookie(
        key=NOMBRE_COOKIE_REFRESH,
        value=str(refresh_token),
        max_age=DURACION_REFRESH * 24 * 60 * 60,  # Convertir a segundos
        httponly=True,
        secure=True,
        samesite='Lax',
        path='/api/v1/auth/refresh/',     # Solo disponible en la ruta de refresco
    )

    return response


def eliminar_cookies_jwt(response):
    """
    Elimina las cookies JWT del navegador del usuario.
    Usado en el endpoint de logout para cerrar sesión.

    Args:
        response: Objeto Response de DRF.

    Returns:
        response con las cookies eliminadas.
    """
    response.delete_cookie(NOMBRE_COOKIE_ACCESS)
    response.delete_cookie(NOMBRE_COOKIE_REFRESH)
    return response


def verificar_rate_limit(ip: str) -> dict:
    """
    Verifica si la IP ha superado el límite de intentos de login.
    Usa Redis como caché para llevar el conteo.

    Args:
        ip (str): Dirección IP del cliente.

    Returns:
        dict con:
            'bloqueado' (bool): True si la IP está bloqueada.
            'intentos'  (int):  Número de intentos fallidos.
            'segundos'  (int):  Segundos restantes del bloqueo.

    Ejemplo:
        estado = verificar_rate_limit('192.168.1.1')
        if estado['bloqueado']:
            return respuesta_error_general("Demasiados intentos.")
    """
    clave_intentos = f'login_intentos:{ip}'
    clave_bloqueo  = f'login_bloqueado:{ip}'

    # Verificar si la IP ya está bloqueada
    segundos_restantes = cache.ttl(clave_bloqueo)
    if segundos_restantes and segundos_restantes > 0:
        return {
            'bloqueado': True,
            'intentos':  MAX_INTENTOS_LOGIN,
            'segundos':  segundos_restantes,
        }

    # Obtener conteo de intentos actuales
    intentos = cache.get(clave_intentos, 0)

    return {
        'bloqueado': False,
        'intentos':  intentos,
        'segundos':  0,
    }


def registrar_intento_fallido(ip: str):
    """
    Registra un intento de login fallido para la IP dada.
    Si supera el límite, bloquea la IP por TIEMPO_BLOQUEO_MIN minutos.

    Args:
        ip (str): Dirección IP del cliente.
    """
    clave_intentos = f'login_intentos:{ip}'
    clave_bloqueo  = f'login_bloqueado:{ip}'

    # Incrementar el contador de intentos
    intentos = cache.get(clave_intentos, 0) + 1
    cache.set(clave_intentos, intentos, timeout=TIEMPO_BLOQUEO_MIN * 60)

    # Si superó el límite, activar el bloqueo
    if intentos >= MAX_INTENTOS_LOGIN:
        cache.set(clave_bloqueo, True, timeout=TIEMPO_BLOQUEO_MIN * 60)


def limpiar_intentos_fallidos(ip: str):
    """
    Limpia el conteo de intentos fallidos para la IP dada.
    Se llama tras un login exitoso.

    Args:
        ip (str): Dirección IP del cliente.
    """
    cache.delete(f'login_intentos:{ip}')
    cache.delete(f'login_bloqueado:{ip}')
