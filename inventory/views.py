from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from sede.models import Sede
from mantenimientos.models import Mantenimiento
from .models import Equipo, Periferico, Licencia, Pasisalvo, HistorialPeriferico, HistorialEquipo, HistorialMovimientoEquipo, ReporteIncidente
from usuarios.models import UserProfile
from usuarios.permissions import IsAdminOrOwnerBySede # <-- IMPORTAR
from django.db.models import Count, Q, F
from .serializers import SedeSerializer, EquipoSerializer, MantenimientoSerializer, PerifericoSerializer, LicenciaSerializer, PasisalvoSerializer, HistorialPerifericoSerializer, HistorialEquipoSerializer, HistorialMovimientoEquipoSerializer, ReporteIncidenteSerializer
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
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede] # <-- APLICAR

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
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede] # <-- APLICAR
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = EquipoFilter

    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Equipo.objects.none()

        # Initialize user_profile to None to avoid UnboundLocalError
        user_profile = None
        
        # 1. Base queryset
        queryset = Equipo.objects.filter(activo=True).order_by('nombre')

        # 2. Check if user is admin
        is_admin = False
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                is_admin = True
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                is_admin = True

        if is_admin:
            # For admins, we let django-filter handle the 'sede' param if present,
            # but we can also handle it manually here safely.
            sede_id = self.request.query_params.get('sede') or self.request.query_params.get('sede_id')
            if sede_id and sede_id.isdigit() and sede_id != '0':
                queryset = queryset.filter(sede_id=sede_id)
            return queryset

        # 3. Apply user-specific filtering for non-admins
        if user_profile and hasattr(user_profile, 'sede') and user_profile.sede:
            # Permitimos ver equipos de su sede O equipos que no tienen sede asignada aún
            return queryset.filter(Q(sede=user_profile.sede) | Q(sede__isnull=True))
        
        return Equipo.objects.none()
    
    def get_permissions(self):
        """
        Instancia y devuelve la lista de permisos que esta vista requiere.
        Para acciones 'list' y 'create', solo se necesita estar autenticado.
        Para otras acciones (retrieve, update, destroy), se aplica el permiso de sede.
        """
        if self.action in ['list', 'create']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede]
        return super().get_permissions()

    def perform_create(self, serializer):
        """
        Asigna el usuario actual como responsable de la entrega al crear un equipo.
        """
        serializer.save(responsable_entrega=self.request.user)

    def perform_update(self, serializer):
        """
        Asigna el usuario actual como responsable si se está asignando un empleado.
        """
        # Si 'empleado_asignado' está en los datos a actualizar y tiene un valor,
        # significa que se está realizando o cambiando una asignación.
        if 'empleado_asignado' in serializer.validated_data and serializer.validated_data['empleado_asignado']:
            serializer.save(responsable_entrega=self.request.user)
        else:
            # Si no se está asignando un empleado, simplemente guarda los demás cambios
            # sin modificar el responsable_entrega existente.
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
            return Response({"detail": f"No se pudo dar de baja el equipo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Filtro para Mantenimientos
class MantenimientoFilter(django_filters.rest_framework.FilterSet):
    class Meta:
        model = Mantenimiento
        fields = ['sede', 'estado_mantenimiento', 'tipo_mantenimiento', 'equipo']

# Vistas para el modelo Mantenimiento
class MantenimientoViewSet(viewsets.ModelViewSet):
    serializer_class = MantenimientoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = MantenimientoFilter

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Mantenimiento.objects.none()

        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                return Mantenimiento.objects.all().order_by('-fecha_inicio')
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                return Mantenimiento.objects.all().order_by('-fecha_inicio')
            return Mantenimiento.objects.none()

        if hasattr(user_profile, 'sede') and user_profile.sede:
            return Mantenimiento.objects.filter(sede=user_profile.sede).order_by('-fecha_inicio')

        return Mantenimiento.objects.none()

    def perform_create(self, serializer):
        instance = serializer.save()
        
        # Obtener la fecha para el próximo mantenimiento del equipo desde los datos validados
        fecha_proximo_mantenimiento_equipo = serializer.validated_data.get('fecha_proximo_mantenimiento_equipo', None)
        
        # Obtener el equipo de forma segura
        equipo = getattr(instance, 'equipo', None)
        
        if equipo:
            # Actualizar la fecha del último mantenimiento del equipo si el estado es 'Finalizado'
            if instance.estado_mantenimiento == 'Finalizado' and instance.fecha_finalizacion:
                equipo.fecha_ultimo_mantenimiento = instance.fecha_finalizacion
            
            # Si se proporcionó una nueva fecha para el próximo mantenimiento, actualizar el equipo
            if fecha_proximo_mantenimiento_equipo:
                equipo.fecha_proximo_mantenimiento = fecha_proximo_mantenimiento_equipo
            
            # Guardar los cambios en el equipo
            equipo.save()

    def perform_update(self, serializer):
        instance = serializer.save()

        # Obtener la fecha para el próximo mantenimiento del equipo desde los datos validados
        fecha_proximo_mantenimiento_equipo = serializer.validated_data.get('fecha_proximo_mantenimiento_equipo', None)
        
        # Obtener el equipo de forma segura
        equipo = getattr(instance, 'equipo', None)
        
        if equipo:
            # Actualizar la fecha del último mantenimiento del equipo si el estado es 'Finalizado'
            if instance.estado_mantenimiento == 'Finalizado' and instance.fecha_finalizacion:
                equipo.fecha_ultimo_mantenimiento = instance.fecha_finalizacion
            
            # Si se proporcionó una nueva fecha para el próximo mantenimiento, actualizar el equipo
            if fecha_proximo_mantenimiento_equipo:
                equipo.fecha_proximo_mantenimiento = fecha_proximo_mantenimiento_equipo
            
            # Guardar los cambios en el equipo
            equipo.save()


# Vistas para el modelo Periferico
class PerifericoListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PerifericoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Asigna automáticamente la sede del usuario al crear un periférico."""
        user = self.request.user
        sede_to_assign = None
        
        # Verificar si el usuario es admin
        is_admin = user.is_staff or user.is_superuser
        try:
            user_profile = user.profile
            if hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN':
                is_admin = True
        except UserProfile.DoesNotExist:
            user_profile = None
        
        if is_admin:
            # Si es admin, permitir asignar cualquier sede (o ninguna)
            # La sede vendrá del request data si se proporciona
            serializer.save()
        else:
            # Si es usuario normal, asignar automáticamente su sede
            try:
                if user_profile and hasattr(user_profile, 'sede') and user_profile.sede:
                    sede_to_assign = user_profile.sede
            except:
                pass
            serializer.save(sede=sede_to_assign)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Periferico.objects.none()

        is_admin = False
        user_profile = None
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                is_admin = True
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                is_admin = True

        queryset = Periferico.objects.all()

        if is_admin:
            sede_id = self.request.query_params.get('sede') or self.request.query_params.get('sede_id')
            if sede_id and sede_id != '0':
                # Filtrar por sede directa O por sede del equipo asociado
                queryset = queryset.filter(
                    Q(sede_id=sede_id) | Q(equipo_asociado__sede_id=sede_id)
                )
            return queryset
        
        if user_profile and hasattr(user_profile, 'sede') and user_profile.sede:
            # Filtrar por sede directa O por sede del equipo asociado
            return queryset.filter(
                Q(sede=user_profile.sede) | Q(equipo_asociado__sede=user_profile.sede)
            )

        return Periferico.objects.none()

class PerifericoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Periferico.objects.all()
    serializer_class = PerifericoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede] # <-- APLICAR

# Vistas para el modelo Licencia
class LicenciaListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LicenciaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Licencia.objects.none()

        is_admin = False
        user_profile = None
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                is_admin = True
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                is_admin = True

        queryset = Licencia.objects.all()

        if is_admin:
            sede_id = self.request.query_params.get('sede') or self.request.query_params.get('sede_id')
            if sede_id and sede_id != '0':
                queryset = queryset.filter(equipo_asociado__sede_id=sede_id)
            return queryset
        
        if user_profile and hasattr(user_profile, 'sede') and user_profile.sede:
            return queryset.filter(equipo_asociado__sede=user_profile.sede)

        return Licencia.objects.none()

class LicenciaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Licencia.objects.all()
    serializer_class = LicenciaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede] # <-- APLICAR

# Vistas para el modelo Pasisalvo
class PasisalvoListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PasisalvoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Asigna automáticamente la sede y el usuario al crear un pasisalvo."""
        user = self.request.user
        sede_to_assign = None
        
        # Verificar si el usuario es admin
        is_admin = user.is_staff or user.is_superuser
        try:
            user_profile = user.profile
            if hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN':
                is_admin = True
        except UserProfile.DoesNotExist:
            user_profile = None
        
        # Determinar la sede a asignar
        if not is_admin and user_profile and hasattr(user_profile, 'sede') and user_profile.sede:
            sede_to_assign = user_profile.sede
        else:
            # Si es admin, intentar obtener la sede del colaborador
            colaborador_id = self.request.data.get('colaborador')
            if colaborador_id:
                try:
                    from empleados.models import Empleado
                    colaborador = Empleado.objects.get(pk=colaborador_id)
                    sede_to_assign = colaborador.sede
                except Empleado.DoesNotExist:
                    pass
        
        serializer.save(generado_por=user, sede=sede_to_assign)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Pasisalvo.objects.none()

        is_admin = False
        user_profile = None
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                is_admin = True
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                is_admin = True

        queryset = Pasisalvo.objects.all().order_by('-fecha_generacion')

        if is_admin:
            sede_id = self.request.query_params.get('sede') or self.request.query_params.get('sede_id')
            if sede_id and sede_id != '0':
                # Filtrar por sede directa O por sede del colaborador
                queryset = queryset.filter(
                    Q(sede_id=sede_id) | Q(colaborador__sede_id=sede_id)
                )
            return queryset
        
        if user_profile and hasattr(user_profile, 'sede') and user_profile.sede:
            # Filtrar por sede directa O por sede del colaborador
            return queryset.filter(
                Q(sede=user_profile.sede) | Q(colaborador__sede=user_profile.sede)
            )

        return Pasisalvo.objects.none()

class PasisalvoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Pasisalvo.objects.all()
    serializer_class = PasisalvoSerializer
    permission_classes = [IsAuthenticated]

# Vista para el Historial de Periféricos
class HistorialPerifericoListAPIView(generics.ListAPIView): 
    queryset = HistorialPeriferico.objects.all()
    serializer_class = HistorialPerifericoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = HistorialPeriferico.objects.all()

        is_admin = False
        user_profile = None
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                is_admin = True
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                is_admin = True
        
        if is_admin:
            # Allow admins to filter by sede_id or sede
            sede_id = self.request.query_params.get('sede_id') or self.request.query_params.get('sede')
            if sede_id and sede_id != '0':
                # Filter by equipment's sede OR employee's sede
                queryset = queryset.filter(
                    Q(equipo_asociado__sede_id=sede_id) | 
                    Q(empleado_asignado__sede_id=sede_id)
                )
            return queryset

        # Non-admins: filter by their own sede
        if user_profile and hasattr(user_profile, 'sede') and user_profile.sede:
             return queryset.filter(
                Q(equipo_asociado__sede=user_profile.sede) | 
                Q(empleado_asignado__sede=user_profile.sede)
            )

        return HistorialPeriferico.objects.none()

class HistorialMovimientoEquipoListAPIView(generics.ListAPIView):
    queryset = HistorialMovimientoEquipo.objects.all()
    serializer_class = HistorialMovimientoEquipoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = HistorialMovimientoEquipo.objects.all()
        
        is_admin = False
        user_profile = None
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                is_admin = True
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                is_admin = True

        if is_admin:
             # Allow admins to filter by sede_id or sede
            sede_id = self.request.query_params.get('sede_id') or self.request.query_params.get('sede')
            if sede_id and sede_id != '0':
                # Filtrar por sede directa, equipo__sede o empleado__sede
                queryset = queryset.filter(
                    Q(sede_id=sede_id) |
                    Q(equipo__sede_id=sede_id) |
                    Q(empleado_asignado__sede_id=sede_id)
                )
            return queryset

        # Si no es admin, filtrar por sede del usuario
        if user_profile and hasattr(user_profile, 'sede') and user_profile.sede:
            # Filtrar por sede directa, equipo__sede o empleado__sede
            return queryset.filter(
                Q(sede=user_profile.sede) |
                Q(equipo__sede=user_profile.sede) |
                Q(empleado_asignado__sede=user_profile.sede)
            )

        return HistorialMovimientoEquipo.objects.none()

from datetime import datetime, timedelta

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        Calcula y devuelve estadísticas clave para el dashboard, filtradas por sede para usuarios no administradores.
        """
        user = request.user
        
        # Definir QuerySets base
        equipos_qs = Equipo.objects.all() # Se incluyen todos para contar los de baja
        mantenimientos_qs = Mantenimiento.objects.all()
        perifericos_qs = Periferico.objects.all()
        licencias_qs = Licencia.objects.all()
        usuarios_qs = User.objects.all()

        is_admin = False
        user_profile = None
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                is_admin = True
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                is_admin = True

        if not is_admin:
            user_sede = getattr(user_profile, 'sede', None)
            if user_sede:
                equipos_qs = equipos_qs.filter(sede=user_sede)
                mantenimientos_qs = mantenimientos_qs.filter(sede=user_sede)
                perifericos_qs = perifericos_qs.filter(equipo_asociado__sede=user_sede)
                licencias_qs = licencias_qs.filter(equipo_asociado__sede=user_sede)
                usuarios_qs = usuarios_qs.filter(profile__sede=user_sede)
            else:
                return Response({"detail": "Usuario sin sede asignada."}, status=403)
        else:
            # Si es admin, puede opcionalmente filtrar por sede_id en la URL
            sede_id = request.query_params.get('sede') or request.query_params.get('sede_id')
            if sede_id and sede_id != '0':
                try:
                    target_sede = Sede.objects.get(id=sede_id)
                    equipos_qs = equipos_qs.filter(sede=target_sede)
                    mantenimientos_qs = mantenimientos_qs.filter(sede=target_sede)
                    perifericos_qs = perifericos_qs.filter(equipo_asociado__sede=target_sede)
                    licencias_qs = licencias_qs.filter(equipo_asociado__sede=target_sede)
                    usuarios_qs = usuarios_qs.filter(profile__sede=target_sede)
                except Sede.DoesNotExist:
                    pass
        
        # QuerySet de equipos activos para la mayoría de las estadísticas
        equipos_activos_qs = equipos_qs.filter(activo=True)

        # Contadores basados en los QuerySets filtrados
        total_equipos = equipos_activos_qs.count()
        equipos_dados_de_baja = equipos_qs.filter(activo=False).count()
        total_mantenimientos = mantenimientos_qs.count()
        total_perifericos = perifericos_qs.count()
        total_licencias = licencias_qs.count()
        total_usuarios = usuarios_qs.count()

        # Estadísticas basadas en los QuerySets filtrados
        equipos_por_estado = equipos_activos_qs.values('estado_tecnico').annotate(count=Count('estado_tecnico'))
        equipos_por_disponibilidad = equipos_activos_qs.values('estado_disponibilidad').annotate(count=Count('estado_disponibilidad'))
        equipos_por_tipo = equipos_activos_qs.values('tipo_equipo').annotate(count=Count('tipo_equipo'))
        
        mantenimientos_por_estado = mantenimientos_qs.values('estado_mantenimiento').annotate(count=Count('estado_mantenimiento'))
        mantenimientos_por_tipo = mantenimientos_qs.values('tipo_mantenimiento').annotate(count=Count('tipo_mantenimiento'))
        
        perifericos_por_tipo = perifericos_qs.values('tipo').annotate(count=Count('tipo'))
        licencias_por_estado = licencias_qs.values('estado').annotate(count=Count('estado'))
        
        # Conteo de mantenimientos "activos" (Pendientes o En proceso)
        mantenimientos_activos = mantenimientos_qs.filter(
            estado_mantenimiento__in=['Pendiente', 'En proceso']
        ).count()

        # Mantenimientos VENCIDOS: Estado Pendiente
        # Ajuste: Si tiene fecha de finalización (estimada), se usa esa como límite.
        today = timezone.now().date()
        mantenimientos_vencidos = mantenimientos_qs.filter(
            estado_mantenimiento='Pendiente'
        ).filter(
            Q(fecha_finalizacion__isnull=False, fecha_finalizacion__lt=today) |
            Q(fecha_finalizacion__isnull=True, fecha_inicio__lt=today)
        ).count()

        # Para los próximos mantenimientos (próximos 30 días)
        proximos_mantenimientos = mantenimientos_qs.filter(
            estado_mantenimiento='Pendiente',
            fecha_inicio__gte=today,
            fecha_inicio__lte=today + timedelta(days=30)
        ).count()

        # Licencias vencidas
        licencias_vencidas = licencias_qs.filter(
            Q(estado='Vencida') | Q(fecha_vencimiento__lt=today)
        ).distinct().count()

        # Licencias por vencer (próximos 30 días)
        licencias_por_vencer = licencias_qs.filter(
            fecha_vencimiento__gte=today,
            fecha_vencimiento__lte=today + timedelta(days=30)
        ).count()

        # Mantenimientos finalizados TARDE
        mantenimientos_finalizados_tarde = mantenimientos_qs.filter(
            estado_mantenimiento='Finalizado',
            fecha_real_finalizacion__gt=F('fecha_finalizacion')
        ).count()

        stats = {
            'total_equipos': total_equipos,
            'equipos_dados_de_baja': equipos_dados_de_baja,
            'total_mantenimientos': total_mantenimientos,
            'total_perifericos': total_perifericos,
            'total_licencias': total_licencias,
            'total_usuarios': total_usuarios,
            'proximos_mantenimientos': proximos_mantenimientos,
            'mantenimientos_activos': mantenimientos_activos,
            'mantenimientos_vencidos': mantenimientos_vencidos,
            'mantenimientos_finalizados_tarde': mantenimientos_finalizados_tarde,
            'licencias_vencidas': licencias_vencidas,
            'licencias_por_vencer': licencias_por_vencer,
            'equipos_por_estado': list(equipos_por_estado),
            'equipos_por_disponibilidad': list(equipos_por_disponibilidad),
            'equipos_por_tipo': list(equipos_por_tipo),
            'mantenimientos_por_estado': list(mantenimientos_por_estado),
            'mantenimientos_por_tipo': list(mantenimientos_por_tipo),
            'perifericos_por_tipo': list(perifericos_por_tipo),
            'licencias_por_estado': list(licencias_por_estado),
        }
        return Response(stats, status=status.HTTP_200_OK)

class HistorialEquipoListView(generics.ListAPIView):
    """
    API view to retrieve the history of changes for a specific equipo.
    """
    serializer_class = HistorialEquipoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede]

    def get_queryset(self):
        """
        This view returns a list of history records for the equipo specified
        in the URL, but first, it checks if the user has permission to view
        the parent 'Equipo' object.
        """
        equipo_pk = self.kwargs['equipo_pk']
        
        # 1. Fetch the parent object.
        try:
            equipo = Equipo.objects.get(pk=equipo_pk)
        except Equipo.DoesNotExist:
            # This will result in a 404 response, which is appropriate.
            # The queryset will be empty and DRF will handle it.
            return HistorialEquipo.objects.none()

        # 2. Manually check permissions on the parent object.
        # This will trigger IsAdminOrOwnerBySede.has_object_permission(..., equipo)
        self.check_object_permissions(self.request, equipo)
        
        # 3. If permission is granted, return the actual queryset.
        return HistorialEquipo.objects.filter(equipo__pk=equipo_pk)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import PerifericoSerializer
from empleados.models import Empleado
from empleados.serializers import EmpleadoSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clearance_info(request, empleado_id):
    try:
        empleado = Empleado.objects.get(pk=empleado_id)
    except Empleado.DoesNotExist:
        return Response({"detail": "Empleado no encontrado"}, status=404)

    equipos_activos = Equipo.objects.filter(empleado_asignado=empleado, activo=True)
    perifericos_activos = Periferico.objects.filter(empleado_asignado=empleado)
    historial_entregas = HistorialMovimientoEquipo.objects.filter(
        empleado_asignado=empleado, 
        fecha_devolucion__isnull=False
    )

    data = {
        "empleado": EmpleadoSerializer(empleado).data,
        "pendientes": {
            "equipos": EquipoSerializer(equipos_activos, many=True).data,
            "perifericos": PerifericoSerializer(perifericos_activos, many=True).data,
        },
        "entregados_historial": HistorialMovimientoEquipoSerializer(historial_entregas, many=True).data,
        "esta_a_paz_y_salvo": equipos_activos.count() == 0 and perifericos_activos.count() == 0
    }
    return Response(data)


class ReporteIncidenteListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/incidentes/          → lista todos los incidentes
    GET  /api/incidentes/?equipo=X → filtra por equipo (usado por el frontend en editar equipo)
    POST /api/incidentes/          → crea un nuevo reporte de incidente
    """
    serializer_class = ReporteIncidenteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ReporteIncidente.objects.all().order_by('-creado_en')
        equipo_id = self.request.query_params.get('equipo')
        if equipo_id:
            queryset = queryset.filter(equipo_id=equipo_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

