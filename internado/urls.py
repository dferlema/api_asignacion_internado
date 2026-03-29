# ============================================================
# URLS.PY — Rutas principales del proyecto
# ============================================================

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from auth_views import LoginView, LogoutView, PerfilView

urlpatterns = [

    # Panel de administración
    path('admin/', admin.site.urls),

    # Autenticación JWT
    path('api/v1/auth/login/',   LoginView.as_view(),        name='auth-login'),
    path('api/v1/auth/logout/',  LogoutView.as_view(),       name='auth-logout'),
    path('api/v1/auth/perfil/',  PerfilView.as_view(),       name='auth-perfil'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/v1/auth/verify/',  TokenVerifyView.as_view(),  name='token-verify'),

    # Módulos del sistema
    path('api/v1/estudiantes/', include('estudiantes.urls')),
    path('api/v1/ranking/',     include('ranking.urls')),
    path('api/v1/plazas/',      include('plazas.urls')),

    # Documentación automática
    path('api/schema/',  SpectacularAPIView.as_view(),                      name='schema'),
    path('api/docs/',    SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/',   SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]
