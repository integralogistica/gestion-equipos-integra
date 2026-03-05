from rest_framework import serializers
from django.contrib.auth.models import User
from sedes.models import Sede  # Asegúrate de que la importación a tu modelo Sede sea correcta

class SedeSerializer(serializers.ModelSerializer):
    """
    Serializador simple para el modelo Sede.
    """
    class Meta:
        model = Sede
        fields = ['id', 'nombre']

class UserDataSerializer(serializers.ModelSerializer):
    """
    Serializador para los datos del usuario que se enviarán al frontend.
    Incluye las sedes a las que el usuario tiene acceso.
    """
    # Este es el campo clave que espera el frontend.
    # Asume que tu modelo User (o un Profile asociado) tiene un campo
    # ManyToManyField llamado 'sedes_autorizadas' que lo relaciona con el modelo Sede.
    sedes_autorizadas = SedeSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'sedes_autorizadas']
