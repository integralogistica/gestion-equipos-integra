from django.shortcuts import render
from rest_framework import generics, status
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
from rest_framework import viewsets

# Vistas para el modelo Sede
class SedeListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    permission_classes = [IsAuthenticated]

class SedeRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede]

class EquipoFilter(django_filters.rest_framework.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=[('overdue', 'Vencido'), ('upcoming', 'Próximo')],
        method='filter_by_status',
        label='Estado de Mantenimiento'
    )

    class Meta:
        model = Equipo
        fields = ['sede', 'estado_tecnico', 'estado_disponibilidad']

    def filter_by_status(self, queryset, name, value):
        today = timezone.now().date()
        if value == 'overdue':
            return queryset.filter(fecha_proximo_mantenimiento__lt=today)
        elif value == 'upcoming':
            return queryset.filter(
                fecha_proximo_mantenimiento__gte=today,
                fecha_proximo_mantenimiento__lte=today + timedelta(days=30)
            )
        return queryset

# Vistas para el modelo Equipo
class EquipoViewSet(viewsets.ModelViewSet):
    serializer_class = EquipoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = EquipoFilter

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Equipo.objects.none()

        user_profile = None
        queryset = Equipo.objects.filter(activo=True).order_by('nombre')
        is_admin = False
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                is_admin = True
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                is_admin = True

        if is_admin:
            sede_id = self.request.query_params.get('sede') or self.request.query_params.get('sede_id')
            if sede_id and sede_id.isdigit() and sede_id != '0':
                queryset = queryset.filter(sede_id=sede_id)
            return queryset

        if user_profile and hasattr(user_profile, 'sede') and user_profile.sede:
            return queryset.filter(sede=user_profile.sede)
        
        return Equipo.objects.none()
    
    def get_permissions(self):
        if self.action in ['list', 'create']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(responsable_entrega=self.request.user)

    def perform_update(self, serializer):
        if 'empleado_asignado' in serializer.validated_data and serializer.validated_data['empleado_asignado']:
            serializer.save(responsable_entrega=self.request.user)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.activo = False
            instance.empleado_asignado = None
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"No se pudo dar de baja el equipo: {str(e)}"}, status=500)

# Vistas para el modelo Mantenimiento
class MantenimientoViewSet(viewsets.ModelViewSet):
    serializer_class = MantenimientoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['sede', 'estado_mantenimiento', 'tipo_mantenimiento', 'equipo']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Mantenimiento.objects.none()
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                return Mantenimiento.objects.all().order_by('-fecha_inicio')
            if hasattr(user_profile, 'sede') and user_profile.sede:
                return Mantenimiento.objects.filter(sede=user_profile.sede).order_by('-fecha_inicio')
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                return Mantenimiento.objects.all().order_by('-fecha_inicio')
        return Mantenimiento.objects.none()

    def perform_create(self, serializer):
        instance = serializer.save()
        fecha_proximo = serializer.validated_data.get('fecha_proximo_mantenimiento_equipo')
        equipo = instance.equipo
        if instance.estado_mantenimiento == 'Finalizado' and instance.fecha_finalizacion:
            equipo.fecha_ultimo_mantenimiento = instance.fecha_finalizacion
        if fecha_proximo:
            equipo.fecha_proximo_mantenimiento = fecha_proximo
        equipo.save()

# Vistas para el modelo Periferico
class PerifericoListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PerifericoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Periferico.objects.all()
        is_admin = user.is_staff or user.is_superuser or (hasattr(user, 'profile') and user.profile.rol == 'ADMIN')
        
        if is_admin:
            sede_id = self.request.query_params.get('sede')
            if sede_id and sede_id != '0':
                queryset = queryset.filter(Q(sede_id=sede_id) | Q(equipo_asociado__sede_id=sede_id))
            return queryset
        
        if hasattr(user, 'profile') and user.profile.sede:
             return queryset.filter(Q(sede=user.profile.sede) | Q(equipo_asociado__sede=user.profile.sede))
        return Periferico.objects.none()

class PerifericoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Periferico.objects.all()
    serializer_class = PerifericoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede]

# Vista para el Dashboard
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        equipos_qs = Equipo.objects.all()
        mantenimientos_qs = Mantenimiento.objects.all()
        licencias_qs = Licencia.objects.all()
        
        is_admin = user.is_staff or user.is_superuser or (hasattr(user, 'profile') and user.profile.rol == 'ADMIN')
        if not is_admin:
            user_sede = getattr(user.profile, 'sede', None)
            if user_sede:
                equipos_qs = equipos_qs.filter(sede=user_sede)
                mantenimientos_qs = mantenimientos_qs.filter(sede=user_sede)
                licencias_qs = licencias_qs.filter(equipo_asociado__sede=user_sede)
        
        today = timezone.now().date()
        stats = {
            'total_equipos': equipos_qs.filter(activo=True).count(),
            'mantenimientos_vencidos': mantenimientos_qs.filter(estado_mantenimiento='Pendiente', fecha_inicio__lt=today).count(),
            'licencias_riesgo_auditoria': licencias_qs.filter(tipo_activacion='Pendiente de Activación').count(),
            'equipos_en_obsolescencia': equipos_qs.filter(estado_tecnico='En Obsolescencia').count(),
        }
        return Response(stats)

class EquipoHistorialMovimientoView(generics.ListAPIView):
    serializer_class = HistorialMovimientoEquipoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        equipo_id = self.request.query_params.get('equipo')
        if equipo_id:
            return HistorialMovimientoEquipo.objects.filter(equipo_id=equipo_id).order_by('-fecha_asignacion')
        return HistorialMovimientoEquipo.objects.all().order_by('-fecha_asignacion')

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

class LicenciaListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LicenciaSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Licencia.objects.all()

class LicenciaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Licencia.objects.all()
    serializer_class = LicenciaSerializer
    permission_classes = [IsAuthenticated]

class PasisalvoListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PasisalvoSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Pasisalvo.objects.all()

class PasisalvoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Pasisalvo.objects.all()
    serializer_class = PasisalvoSerializer
    permission_classes = [IsAuthenticated]

class HistorialPerifericoListAPIView(generics.ListAPIView):
    serializer_class = HistorialPerifericoSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return HistorialPeriferico.objects.all()

class HistorialEquipoListView(generics.ListAPIView):
    serializer_class = HistorialEquipoSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        equipo_pk = self.kwargs.get('equipo_pk')
        return HistorialEquipo.objects.filter(equipo_id=equipo_pk)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clearance_info(request, empleado_id):
    return Response({"status": "ok"})
