from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

# Serializers for Usuario app
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['cargo', 'area']

    def update(self, instance, validated_data):
        print(f"DEBUG_UserProfileSerializer: Recibiendo validated_data para UserProfile: {validated_data}")
        # Call the superclass update method to handle the actual saving
        return super().update(instance, validated_data)

class UserSerializer(serializers.ModelSerializer):
    cargo = serializers.SerializerMethodField()
    area = serializers.SerializerMethodField()
    rol = serializers.SerializerMethodField()
    sede_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    sede = serializers.SerializerMethodField(read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_superuser', 'sede', 'sede_id', 'cargo', 'area', 'rol', 'password']

    def get_cargo(self, obj):
        try:
            return obj.profile.cargo
        except UserProfile.DoesNotExist:
            return None

    def get_area(self, obj):
        try:
            return obj.profile.area
        except UserProfile.DoesNotExist:
            return None

    def get_rol(self, obj):
        try:
            return obj.profile.rol
        except UserProfile.DoesNotExist:
            return 'USUARIO'

    def get_sede(self, obj):
        try:
            profile = obj.profile
            if profile.sede:
                return {
                    'id': profile.sede.id,
                    'nombre': profile.sede.nombre
                }
        except UserProfile.DoesNotExist:
            pass
        return None

    def create(self, validated_data):
        # Usar initial_data para campos que no están en el modelo y son SerializerMethodField
        cargo = self.initial_data.get('cargo')
        area = self.initial_data.get('area')
        rol = self.initial_data.get('rol', 'USUARIO')
        sede_id = validated_data.pop('sede_id', None)
        password = validated_data.pop('password', None)
        
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        
        # El signal crea el perfil automáticamente
        profile = user.profile
        profile.cargo = cargo
        profile.area = area
        profile.rol = rol
        if sede_id:
            from sede.models import Sede
            try:
                profile.sede = Sede.objects.get(id=sede_id)
            except Sede.DoesNotExist:
                pass
        profile.save()
        return user

    def update(self, instance, validated_data):
        # Usar initial_data para campos que no están en el modelo y son SerializerMethodField
        cargo = self.initial_data.get('cargo', 'no_change')
        area = self.initial_data.get('area', 'no_change')
        rol = self.initial_data.get('rol', 'no_change')
        sede_id = validated_data.pop('sede_id', 'no_change')
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        instance.save()
        
        profile = instance.profile
        if cargo != 'no_change': profile.cargo = cargo
        if area != 'no_change': profile.area = area
        if rol != 'no_change': profile.rol = rol
        
        if sede_id != 'no_change':
            if sede_id is None:
                profile.sede = None
            else:
                from sede.models import Sede
                try:
                    profile.sede = Sede.objects.get(id=sede_id)
                except Sede.DoesNotExist:
                    profile.sede = None
        
        profile.save()
        return instance
