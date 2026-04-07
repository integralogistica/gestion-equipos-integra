from django.shortcuts import render
from rest_framework import generics, status, viewsets
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta, date
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from sede.models import Sede
from mantenimientos.models import Mantenimiento
from .models import Equipo, Periferico, Licencia, Pasisalvo, HistorialPeriferico, HistorialEquipo, HistorialMovimientoEquipo, ReporteIncidente
from usuarios.models import UserProfile
from usuarios.permissions import IsAdminOrOwnerBySede 
from django.db.models import Count, Q, F
from .serializers import (
    SedeSerializer, EquipoSerializer, MantenimientoSerializer, 
    PerifericoSerializer, LicenciaSerializer, PasisalvoSerializer, 
    HistorialPerifericoSerializer, HistorialEquipoSerializer, 
    HistorialMovimientoEquipoSerializer, ReporteIncidenteSerializer
)
import django_filters.rest_framework

# --- Estadísticas del Dashboard ME ---
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        today = timezone.now().date()
        
        # Filtros de Sede
        equipos_qs = Equipo.objects.all()
        mantenimientos_qs = Mantenimiento.objects.all()
        licencias_qs = Licencia.objects.all()
        
        # Lógica de Permisos de Sede
        is_admin = user.is_staff or user.is_superuser or (hasattr(user, 'profile') and user.profile.rol == 'ADMIN')
        if not is_admin:
            user_sede = getattr(user.profile, 'sede', None)
            if user_sede:
                equipos_qs = equipos_qs.filter(sede=user_sede)
                mantenimientos_qs = mantenimientos_qs.filter(sede=user_sede)
                licencias_qs = licencias_qs.filter(equipo_asociado__sede=user_sede)

        stats = {
            'total_equipos': equipos_qs.filter(activo=True).count(),
            'mantenimientos_vencidos': mantenimientos_qs.filter(estado_mantenimiento='Pendiente', fecha_inicio__lt=today).count(),
            'licencias_riesgo_auditoria': licencias_qs.filter(tipo_activacion='Pendiente de Activación').count(),
            'equipos_en_obsolescencia': equipos_qs.filter(estado_tecnico='En Obsolescencia').count(),
            'licencias_por_activacion': list(licencias_qs.values('tipo_activacion').annotate(count=Count('id'))),
            'equipos_por_estado': list(equipos_qs.filter(activo=True).values('estado_tecnico').annotate(count=Count('id'))),
        }
        return Response(stats)

# --- Gestión de Incidentes / Siniestros ---
class ReporteIncidenteViewSet(viewsets.ModelViewSet):
    queryset = ReporteIncidente.objects.all()
    serializer_class = ReporteIncidenteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ReporteIncidente.objects.all().order_by('-fecha_incidente')
        equipo_id = self.request.query_params.get('equipo')
        if equipo_id:
            queryset = queryset.filter(equipo_id=equipo_id)
        return queryset

    def perform_create(self, serializer):
        equipo = serializer.validated_data.get('equipo')
        serializer.save(creado_por=self.request.user, empleado=equipo.empleado_asignado)

# --- Historial de Movimientos (Línea de Vida) ---
class EquipoHistorialMovimientoView(generics.ListAPIView):
    serializer_class = HistorialMovimientoEquipoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        equipo_id = self.request.query_params.get('equipo')
        if equipo_id:
            return HistorialMovimientoEquipo.objects.filter(equipo_id=equipo_id).order_by('-fecha_asignacion')
        return HistorialMovimientoEquipo.objects.all()

# --- Vistas Estándar de Equipo ---
class EquipoViewSet(viewsets.ModelViewSet):
    serializer_class = EquipoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        # Simplificado para asegurar carga
        return Equipo.objects.filter(activo=True).order_by('nombre')

    def perform_create(self, serializer):
        serializer.save(responsable_entrega=self.request.user)

# --- Otras Vistas Necesarias ---
class SedeListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sede.objects.all(); serializer_class = SedeSerializer
class MantenimientoViewSet(viewsets.ModelViewSet):
    queryset = Mantenimiento.objects.all(); serializer_class = MantenimientoSerializer
class PerifericoListCreateAPIView(generics.ListCreateAPIView):
    queryset = Periferico.objects.all(); serializer_class = PerifericoSerializer
class PerifericoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Periferico.objects.all(); serializer_class = PerifericoSerializer
class LicenciaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Licencia.objects.all(); serializer_class = LicenciaSerializer
class LicenciaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Licencia.objects.all(); serializer_class = LicenciaSerializer
class PasisalvoListCreateAPIView(generics.ListCreateAPIView):
    queryset = Pasisalvo.objects.all(); serializer_class = PasisalvoSerializer
class HistorialPerifericoListAPIView(generics.ListAPIView):
    queryset = HistorialPeriferico.objects.all(); serializer_class = HistorialPerifericoSerializer
class HistorialEquipoListView(generics.ListAPIView):
    serializer_class = HistorialEquipoSerializer
    def get_queryset(self): return HistorialEquipo.objects.filter(equipo_id=self.kwargs['equipo_pk'])
