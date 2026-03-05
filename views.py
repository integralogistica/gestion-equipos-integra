from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from serializers import UserDataSerializer

class CustomAuthToken(ObtainAuthToken):
    """
    Vista de login personalizada que devuelve el token y los datos del usuario.
    """
    def post(self, request, *args, **kwargs):
        # Llama al método original para validar usuario/contraseña y obtener el usuario.
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Crea o recupera el token para ese usuario.
        token, created = Token.objects.get_or_create(user=user)
        
        # Serializa los datos del usuario usando nuestro serializador personalizado.
        user_data = UserDataSerializer(user).data
        
        # Devuelve la respuesta que el frontend espera.
        return Response({
            'token': token.key,
            'user': user_data
        })
