from rest_framework.routers import DefaultRouter
from .views import MantenimientoViewSet, EvidenciaMantenimientoViewSet, HistorialAccionMantenimientoListAPIView
from django.urls import path, include

router = DefaultRouter()
router.register(r'', MantenimientoViewSet, basename='mantenimiento')
router.register(r'evidencias', EvidenciaMantenimientoViewSet, basename='evidencia-mantenimiento')

urlpatterns = [
    path('historial-acciones/', HistorialAccionMantenimientoListAPIView.as_view(), name='mantenimiento-historial-acciones'),
    path('', include(router.urls)),
]