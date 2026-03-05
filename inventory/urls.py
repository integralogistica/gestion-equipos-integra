from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as authtoken_views
from .views import (
    SedeListCreateAPIView, SedeRetrieveUpdateDestroyAPIView,
    EquipoViewSet,
    PerifericoListCreateAPIView, PerifericoRetrieveUpdateDestroyAPIView,
    LicenciaListCreateAPIView, LicenciaRetrieveUpdateDestroyAPIView,
    PasisalvoListCreateAPIView, PasisalvoRetrieveUpdateDestroyAPIView,
    DashboardStatsView, HistorialPerifericoListAPIView, HistorialEquipoListView, HistorialMovimientoEquipoListAPIView,
    clearance_info
)

# Crear un router y registrar nuestros viewsets con él.
router = DefaultRouter()
router.register(r'equipos', EquipoViewSet, basename='equipo')

# El API URLs ahora son determinadas automáticamente por el router.
urlpatterns = [
    # URLs para Equipos (rutas adicionales)
    path('equipos/historial/', HistorialMovimientoEquipoListAPIView.as_view(), name='historial-equipo-movimiento-list'),
    path('equipos/<int:equipo_pk>/historial/', HistorialEquipoListView.as_view(), name='equipo-historial-list'),

    # URLs para Sedes
    path('sedes/', SedeListCreateAPIView.as_view(), name='sede-list-create'),
    path('sedes/<int:pk>/', SedeRetrieveUpdateDestroyAPIView.as_view(), name='sede-detail'),

    path('', include(router.urls)),

    # URLs para Perifericos
    path('perifericos/', PerifericoListCreateAPIView.as_view(), name='periferico-list-create'),
    path('perifericos/<int:pk>/', PerifericoRetrieveUpdateDestroyAPIView.as_view(), name='periferico-detail'),
    path('perifericos/historial/', HistorialPerifericoListAPIView.as_view(), name='historial-periferico-list'),

    # URLs para Licencias
    path('licencias/', LicenciaListCreateAPIView.as_view(), name='licencia-list-create'),
    path('licencias/<int:pk>/', LicenciaRetrieveUpdateDestroyAPIView.as_view(), name='licencia-detail'),

    # URLs para Paz y Salvo
    path('pasisalvos/', PasisalvoListCreateAPIView.as_view(), name='pasisalvo-list-create'),
    path('pasisalvos/<int:pk>/', PasisalvoRetrieveUpdateDestroyAPIView.as_view(), name='pasisalvo-detail'),
    path('pasisalvos/empleado/<int:empleado_id>/info/', clearance_info, name='clearance-info'),

    # URL para obtener el token de autenticación
    path('api-token-auth/', authtoken_views.obtain_auth_token, name='api_token_auth'),

    # URL para las estadísticas del Dashboard
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
