# usuarios/views.py
from rest_framework import generics
from django.contrib.auth.models import User
from .serializers import UserSerializer, UserProfileSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsAdminOrSelf
from .models import UserProfile
from sede.models import Sede
from rest_framework import viewsets
from rest_framework.decorators import action

class UserProfileUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSelf]
    lookup_field = 'user_id'
    lookup_url_kwarg = 'user_pk'

class UserListAPIView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                return User.objects.all()
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                return User.objects.all()
            return User.objects.filter(pk=user.pk) # Un usuario sin perfil solo se ve a sí mismo

        user_sede = getattr(user_profile, 'sede', None)
        if user_sede:
            return User.objects.filter(profile__sede=user_sede)
        
        # Si no es admin y no tiene sede, solo se ve a sí mismo
        return User.objects.filter(pk=user.pk)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or (hasattr(user, 'profile') and user.profile.rol == 'ADMIN'):
            return User.objects.all()
        return User.objects.filter(pk=user.pk)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(old_password):
            return Response({'error': 'La contraseña antigua es incorrecta.'}, status=400)
        
        user.set_password(new_password)
        user.save()
        return Response({'status': 'Contraseña actualizada con éxito.'})

class CustomAuthToken(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Asegurarse de que el perfil exista
        profile, profile_created = UserProfile.objects.get_or_create(user=user)

        sede_info = {'id': profile.sede.id, 'nombre': profile.sede.nombre} if profile.sede else {'id': None, 'nombre': None}
        
        sedes_autorizadas = []
        if user.is_superuser:
            # Superusuario tiene acceso a todas las sedes
            sedes_autorizadas = list(Sede.objects.all().values('id', 'nombre'))
        elif profile.sede:
            # Usuario normal tiene acceso solo a su sede
            sedes_autorizadas = [sede_info]

        return Response({
            'token': token.key,
            'user': {
                'id': user.pk,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'rol': getattr(profile, 'rol', None),
                'sede': sede_info,
                'sedes_autorizadas': sedes_autorizadas
            }
        })
