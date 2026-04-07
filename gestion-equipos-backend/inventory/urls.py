from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EquipoViewSet, ReporteIncidenteViewSet, DashboardStatsView,
    EquipoHistorialMovimientoView, HistorialEquipoListView,
    SedeListCreateAPIView, MantenimientoViewSet, PerifericoListCreateAPIView,
    LicenciaListCreateAPIView, PasisalvoListCreateAPIView, HistorialPerifericoListAPIView
)

router = DefaultRouter()
router.register(r'equipos', EquipoViewSet, basename='equipo')
router.register(r'incidentes', ReporteIncidenteViewSet, basename='incidente')
router.register(r'mantenimientos', MantenimientoViewSet, basename='mantenimiento')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('equipos/historial/', EquipoHistorialMovimientoView.as_view(), name='equipo-historial-movimientos'),
    path('equipos/<int:equipo_pk>/historial/', HistorialEquipoListView.as_view(), name='equipo-historial-cambios'),
    path('sedes/', SedeListCreateAPIView.as_view()),
    path('perifericos/', PerifericoListCreateAPIView.as_view()),
    path('licencias/', LicenciaListCreateAPIView.as_view()),
    path('pasisalvos/', PasisalvoListCreateAPIView.as_view()),
    path('perifericos/historial/', HistorialPerifericoListAPIView.as_view()),
]
