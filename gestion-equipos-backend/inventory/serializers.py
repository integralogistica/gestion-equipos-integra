from django.contrib.auth.models import User
from rest_framework import serializers
from sede.models import Sede
from mantenimientos.models import Mantenimiento
from .models import Equipo, Periferico, Licencia, Pasisalvo, HistorialEquipo, HistorialMovimientoEquipo, ReporteIncidente, HistorialPeriferico
from usuarios.serializers import UserSerializer

class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede; fields = '__all__'

class EquipoSerializer(serializers.ModelSerializer):
    sede_nombre = serializers.CharField(source='sede.nombre', read_only=True)
    class Meta:
        model = Equipo; fields = '__all__'

class MantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mantenimiento; fields = '__all__'

class PerifericoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Periferico; fields = '__all__'

class LicenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licencia; fields = '__all__'

class PasisalvoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pasisalvo; fields = '__all__'

class HistorialPerifericoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialPeriferico; fields = '__all__'

class HistorialEquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialEquipo; fields = '__all__'

class HistorialMovimientoEquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialMovimientoEquipo; fields = '__all__'

class ReporteIncidenteSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)
    class Meta:
        model = ReporteIncidente; fields = '__all__'
