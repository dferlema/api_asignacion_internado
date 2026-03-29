# ============================================================
# MIDDLEWARE.PY — ThreadLocal para request actual
# Permite acceder al request (usuario, IP) desde cualquier
# capa del sistema sin necesidad de pasarlo como parámetro.
# ============================================================

import threading

# Variable local al hilo: cada petición HTTP tiene la suya
_request_local = threading.local()


def obtener_request_actual():
    """
    Retorna el request HTTP activo en el hilo actual.
    Retorna None si no hay request (ej: comandos de manage.py).

    Uso en cualquier archivo del proyecto:
        from helpers.middleware import obtener_request_actual
        request = obtener_request_actual()
        usuario = request.user if request else None
    """
    return getattr(_request_local, 'request', None)


class RequestMiddleware:
    """
    Middleware que almacena el request HTTP actual en el
    ThreadLocal. Debe registrarse en MIDDLEWARE de settings.py
    como primer elemento para que esté disponible en todo el stack.

    Esto permite que ModelBase.save() acceda al usuario e IP
    sin necesidad de recibir el request como parámetro.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Guardar el request en el ThreadLocal antes de procesar
        _request_local.request = request

        # Procesar la petición normalmente
        response = self.get_response(request)

        # Limpiar el ThreadLocal después de responder
        # Evita memory leaks en entornos con reutilización de hilos
        if hasattr(_request_local, 'request'):
            del _request_local.request

        return response
