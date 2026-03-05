from .models import Mantenimiento, EvidenciaMantenimiento, HistorialAccionMantenimiento
from .serializers import MantenimientoSerializer, HistorialAccionMantenimientoSerializer
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from datetime import date
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from usuarios.permissions import IsAdminOrOwnerBySede
from usuarios.models import UserProfile

class MantenimientoViewSet(viewsets.ModelViewSet):
    serializer_class = MantenimientoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede]

    def get_queryset(self):
        user = self.request.user
        queryset = Mantenimiento.objects.prefetch_related('evidencias').select_related('equipo', 'sede', 'responsable')

        # Aplicar filtro de estado_mantenimiento si está en los parámetros
        estado_param = self.request.query_params.get('estado_mantenimiento')
        if estado_param:
            queryset = queryset.filter(estado_mantenimiento=estado_param)

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
            sede_id = self.request.query_params.get('sede_id') or self.request.query_params.get('sede')
            if sede_id and sede_id != '0':
                queryset = queryset.filter(sede_id=sede_id)
            return queryset.order_by('-fecha_inicio')

        user_sede = getattr(user_profile, 'sede', None)
        if user_sede:
            return queryset.filter(Q(sede=user_sede) | Q(responsable=user)).distinct().order_by('-fecha_inicio')
        
        return queryset.filter(responsable=user).order_by('-fecha_inicio')

    def get_permissions(self):
        if self.action in ['list', 'create', 'proximos', 'historial', 'finalizar', 'iniciar_proceso']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def proximos(self, request):
        today = date.today()
        # Ajusta el queryset para ser consistente con get_queryset
        base_queryset = self.get_queryset()
        queryset = base_queryset.filter(
            Q(fecha_inicio__gte=today) | Q(fecha_finalizacion__isnull=True, fecha_inicio__gte=today),
            ~Q(estado_mantenimiento='Finalizado')
        ).order_by('fecha_inicio')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def historial(self, request):
        # Ajusta el queryset para ser consistente con get_queryset
        base_queryset = self.get_queryset()
        queryset = base_queryset.filter(estado_mantenimiento='Finalizado').order_by('-fecha_finalizacion', '-fecha_inicio')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.estado_mantenimiento in ['Finalizado', 'Cancelado']:
            return Response(
                {'error': f'Un mantenimiento en estado "{instance.estado_mantenimiento}" no puede ser modificado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        
        # Si se está marcando como finalizado desde el update general
        if data.get('estado_mantenimiento') == 'Finalizado' or data.get('fecha_finalizacion'):
            if not instance.fecha_real_finalizacion:
                instance.fecha_real_finalizacion = timezone.now().date()
            data['estado_mantenimiento'] = 'Finalizado'

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def iniciar_proceso(self, request, pk=None):
        """
        Cambia el estado de un mantenimiento a 'En proceso'.
        """
        instance = self.get_object()

        if instance.estado_mantenimiento != 'Pendiente':
            return Response(
                {'error': f'El mantenimiento debe estar en estado "Pendiente" para iniciar el proceso. Estado actual: {instance.estado_mantenimiento}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.estado_mantenimiento = 'En proceso'
        instance.save(update_fields=['estado_mantenimiento'])
        
        # Registrar en el historial
        from .models import HistorialAccionMantenimiento
        HistorialAccionMantenimiento.objects.create(
            mantenimiento=instance,
            usuario=request.user,
            accion="Inició proceso",
            detalle=f"El técnico {request.user.username} cambió el estado a 'En proceso'."
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """
        Finaliza un mantenimiento y guarda la evidencia de finalización
        """
        instance = self.get_object()

        if instance.estado_mantenimiento == 'Finalizado':
            return Response(
                {'error': 'Este mantenimiento ya está finalizado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if instance.estado_mantenimiento == 'Cancelado':
            return Response(
                {'error': 'Un mantenimiento cancelado no puede ser finalizado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener el archivo de evidencia de finalización (opcional u obligatorio según requerimiento, aquí lo mantenemos como en el original)
        evidencia_file = request.FILES.get('evidencia_finalizacion')
        if not evidencia_file:
            return Response(
                {'error': 'Debes adjuntar un archivo de evidencia de finalización.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el mantenimiento
        instance.estado_mantenimiento = 'Finalizado'
        # IMPORTANTE: Guardamos en fecha_real_finalizacion, NO sobreescribimos fecha_finalizacion
        instance.fecha_real_finalizacion = timezone.now().date()
        instance.evidencia_finalizacion = evidencia_file
        instance.save()

        # Registrar en el historial
        from .models import HistorialAccionMantenimiento
        HistorialAccionMantenimiento.objects.create(
            mantenimiento=instance,
            usuario=request.user,
            accion="Finalizó mantenimiento",
            detalle=f"El técnico {request.user.username} marcó el mantenimiento como finalizado."
        )

        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        instance = self.get_object()

        if instance.estado_mantenimiento == 'Finalizado':
            return Response(
                {'error': 'Un mantenimiento finalizado no puede ser cancelado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if instance.estado_mantenimiento == 'Cancelado':
            return Response({'status': 'El mantenimiento ya estaba cancelado.'}, status=status.HTTP_200_OK)

        instance.estado_mantenimiento = 'Cancelado'
        instance.save(update_fields=['estado_mantenimiento'])
        
        # Registrar en el historial
        from .models import HistorialAccionMantenimiento
        HistorialAccionMantenimiento.objects.create(
            mantenimiento=instance,
            usuario=request.user,
            accion="Canceló mantenimiento",
            detalle=f"Acción realizada por {request.user.username}."
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class EvidenciaMantenimientoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrOwnerBySede]

    def destroy(self, request, pk=None):
        try:
            evidencia = EvidenciaMantenimiento.objects.get(pk=pk)
            
            # Check permissions
            mantenimiento = evidencia.mantenimiento
            user_profile = request.user.profile

            # Only allow deletion if user is admin/superuser, or admin of the maintenance's sede
            if not (request.user.is_staff or request.user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN' and user_profile.sede == mantenimiento.sede)):
                 return Response({'error': 'No tienes permiso para eliminar esta evidencia.'}, status=status.HTTP_403_FORBIDDEN)

            evidencia.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except EvidenciaMantenimiento.DoesNotExist:
            return Response({'error': 'La evidencia no fue encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HistorialAccionMantenimientoListAPIView(generics.ListAPIView):
    serializer_class = HistorialAccionMantenimientoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = HistorialAccionMantenimiento.objects.select_related('mantenimiento', 'mantenimiento__equipo', 'usuario')
        
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
            sede_id = self.request.query_params.get('sede_id') or self.request.query_params.get('sede')
            if sede_id and sede_id != '0':
                queryset = queryset.filter(mantenimiento__sede_id=sede_id)
            return queryset.order_by('-fecha')

        user_sede = getattr(user_profile, 'sede', None)
        if user_sede:
            return queryset.filter(mantenimiento__sede=user_sede).order_by('-fecha')
        
        return queryset.filter(usuario=user).order_by('-fecha')