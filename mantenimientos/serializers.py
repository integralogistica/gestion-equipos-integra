from rest_framework import serializers
from django.utils import timezone
from .models import Mantenimiento, EvidenciaMantenimiento, HistorialAccionMantenimiento
from inventory.models import Equipo
from django.contrib.auth.models import User
from sede.models import Sede
import os


class MultipleFileField(serializers.ListField):
    """
    Campo personalizado para manejar múltiples archivos desde request.FILES
    """
    def to_internal_value(self, data):
        # Si data es una lista de archivos, la retornamos directamente
        if isinstance(data, list):
            # Validamos que todos los elementos sean archivos
            validated_files = []
            for item in data:
                if hasattr(item, 'read'):
                    validated_files.append(item)
            if validated_files:
                return validated_files
        
        # Si data es un solo archivo, lo convertimos a lista
        if hasattr(data, 'read'):
            return [data]
        
        # Si data es None, vacío o cualquier otro tipo, retornamos lista vacía
        # Los archivos se obtendrán desde el método to_internal_value del serializer
        return []

class EvidenciaMantenimientoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo EvidenciaMantenimiento.
    """
    archivo_url = serializers.SerializerMethodField()
    archivo_filename = serializers.SerializerMethodField()

    class Meta:
        model = EvidenciaMantenimiento
        fields = ['id', 'archivo', 'archivo_url', 'archivo_filename']

    def get_archivo_url(self, obj):
        request = self.context.get('request') if self.context else None
        if obj.archivo and hasattr(obj.archivo, 'url'):
            return request.build_absolute_uri(obj.archivo.url) if request else obj.archivo.url
        return None

    def get_archivo_filename(self, obj):
        if obj.archivo and hasattr(obj.archivo, 'name'):
            return os.path.basename(obj.archivo.name)
        return None

class MantenimientoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Mantenimiento, ahora con soporte para múltiples evidencias.
    """
    # Campos anidados para información relacionada
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True, allow_null=True)
    equipo_tipo = serializers.CharField(source='equipo.tipo_equipo', read_only=True, allow_null=True)
    responsable_nombre = serializers.SerializerMethodField()
    sede_nombre = serializers.CharField(source='sede.nombre', read_only=True, allow_null=True)
    
    # Campos adicionales para compatibilidad con el frontend
    equipo_asociado_nombre = serializers.CharField(source='equipo.nombre', read_only=True, allow_null=True)
    usuario_responsable_username = serializers.SerializerMethodField()
    
    def get_responsable_nombre(self, obj):
        if obj.responsable:
            return obj.responsable.get_full_name() or obj.responsable.username
        return None
    
    def get_usuario_responsable_username(self, obj):
        if obj.responsable:
            return obj.responsable.username
        return None
    
    # Campo para mostrar las evidencias existentes (solo lectura)
    evidencias = EvidenciaMantenimientoSerializer(many=True, read_only=True, required=False)
    
    # Campo para subir nuevas evidencias (solo escritura)
    evidencias_uploads = MultipleFileField(
        child=serializers.FileField(max_length=1000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False # No siempre se suben archivos nuevos, especialmente en la actualización
    )
    
    # Campo para evidencia de finalización
    evidencia_finalizacion = serializers.FileField(required=False, allow_null=True, write_only=True)
    evidencia_finalizacion_url = serializers.SerializerMethodField()
    evidencia_finalizacion_filename = serializers.SerializerMethodField()
    
    # Campo calculado para saber si se entregó tarde
    fuera_de_fecha = serializers.ReadOnlyField()

    def get_evidencia_finalizacion_url(self, obj):
        if obj.evidencia_finalizacion:
            request = self.context.get('request') if self.context else None
            if request:
                return request.build_absolute_uri(obj.evidencia_finalizacion.url)
            return obj.evidencia_finalizacion.url
        return None
    
    def get_evidencia_finalizacion_filename(self, obj):
        if obj.evidencia_finalizacion:
            return os.path.basename(obj.evidencia_finalizacion.name)
        return None

    class Meta:
        model = Mantenimiento
        fields = [
            'id', 'equipo', 'equipo_nombre', 'equipo_tipo', 'equipo_asociado_nombre', 'sede', 'sede_nombre',
            'responsable', 'responsable_nombre', 'usuario_responsable_username',
            'tipo_mantenimiento', 'estado_mantenimiento',
            'fecha_inicio', 'fecha_finalizacion', 'fecha_real_finalizacion', 'fuera_de_fecha',
            'descripcion_problema', 'acciones_realizadas', 'repuestos_utilizados',
            'notas', 'creado_en', 'actualizado_en',
            'evidencias', 'evidencias_uploads',
            'evidencia_finalizacion', 'evidencia_finalizacion_url', 'evidencia_finalizacion_filename'
        ]
        read_only_fields = ('creado_en', 'actualizado_en', 'fecha_inicio', 'fecha_real_finalizacion')

    def to_internal_value(self, data):
        """
        Sobrescribimos este método para obtener los archivos directamente de request.FILES
        Este método solo se ejecuta en operaciones de escritura (POST, PUT, PATCH)
        """
        # Verificamos que data sea un diccionario o QueryDict (no una instancia del modelo)
        if not isinstance(data, (dict, type(None))) and not hasattr(data, '__iter__'):
            # Si data no es un diccionario/QueryDict, llamamos al método padre directamente
            return super().to_internal_value(data)
        
        # Obtenemos el request del contexto
        request = None
        if hasattr(self, 'context') and self.context:
            request = self.context.get('request')
        
        # Si hay archivos en request.FILES y no están en data, los agregamos
        if request and hasattr(request, 'FILES'):
            try:
                files = request.FILES.getlist('evidencias_uploads')
                if files:
                    # Creamos una copia mutable de data si es necesario (QueryDict)
                    if hasattr(data, '_mutable'):
                        data._mutable = True
                    # Agregamos los archivos a data solo si no están ya presentes
                    if 'evidencias_uploads' not in data:
                        if isinstance(data, dict):
                            data['evidencias_uploads'] = files
                        elif hasattr(data, '__setitem__'):
                            data['evidencias_uploads'] = files
            except (AttributeError, KeyError):
                # Si hay algún error al obtener los archivos, continuamos sin ellos
                pass
        
        # Llamamos al método padre para validar todos los campos
        try:
            ret = super().to_internal_value(data)
            
            # Si después de la validación no hay evidencias_uploads pero hay archivos en el request, los agregamos
            if ('evidencias_uploads' not in ret or not ret.get('evidencias_uploads')):
                if request and hasattr(request, 'FILES'):
                    try:
                        files = request.FILES.getlist('evidencias_uploads')
                        if files:
                            ret['evidencias_uploads'] = files
                    except (AttributeError, KeyError):
                        pass
            
            return ret
        except Exception as e:
            # Si hay algún error, lo propagamos
            raise e

    def validate(self, data):
        # La validación de la fecha de finalización sigue siendo la misma
        fecha_finalizacion = data.get('fecha_finalizacion')
        if not fecha_finalizacion:
            return data
        
        fecha_inicio_a_comparar = self.instance.fecha_inicio if self.instance else timezone.now().date()
        if fecha_finalizacion < fecha_inicio_a_comparar:
            raise serializers.ValidationError("La fecha de finalización no puede ser anterior a la fecha de inicio.")

        return data

    def create(self, validated_data):
        evidencias_data = validated_data.pop('evidencias_uploads', [])
        mantenimiento = Mantenimiento.objects.create(**validated_data)
        
        for archivo in evidencias_data:
            EvidenciaMantenimiento.objects.create(mantenimiento=mantenimiento, archivo=archivo)
            
        return mantenimiento

    def update(self, instance, validated_data):
        evidencias_data = validated_data.pop('evidencias_uploads', [])
        
        # Actualizar campos del mantenimiento
        instance = super().update(instance, validated_data)
        
        # Añadir nuevas evidencias si se subieron
        for archivo in evidencias_data:
            EvidenciaMantenimiento.objects.create(mantenimiento=instance, archivo=archivo)
            
        return instance
    
    def to_representation(self, instance):
        """
        Sobrescribimos para manejar errores durante la serialización
        """
        try:
            data = super().to_representation(instance)
            return data
        except Exception as e:
            # Si hay un error al serializar, intentamos sin las evidencias
            import traceback
            print(f"ERROR al serializar mantenimiento {instance.id}: {str(e)}")
            print(traceback.format_exc())
            try:
                # Crear una representación básica sin evidencias
                evidencias_data = []
                try:
                    # Intentar obtener evidencias manualmente
                    for evidencia in instance.evidencias.all():
                        evidencias_data.append({
                            'id': evidencia.id,
                            'archivo': str(evidencia.archivo) if evidencia.archivo else None,
                            'archivo_url': None,
                            'archivo_filename': None
                        })
                except Exception as ev_error:
                    print(f"ERROR al obtener evidencias: {str(ev_error)}")
                
                responsable_nombre = None
                usuario_responsable_username = None
                if instance.responsable:
                    responsable_nombre = instance.responsable.get_full_name() or instance.responsable.username
                    usuario_responsable_username = instance.responsable.username
                
                evidencia_finalizacion_url = None
                evidencia_finalizacion_filename = None
                if instance.evidencia_finalizacion:
                    evidencia_finalizacion_filename = os.path.basename(instance.evidencia_finalizacion.name)
                    try:
                        request = self.context.get('request') if self.context else None
                        if request:
                            evidencia_finalizacion_url = request.build_absolute_uri(instance.evidencia_finalizacion.url)
                        else:
                            evidencia_finalizacion_url = instance.evidencia_finalizacion.url
                    except:
                        pass
                
                data = {
                    'id': instance.id,
                    'equipo': instance.equipo.id if instance.equipo else None,
                    'equipo_nombre': instance.equipo.nombre if instance.equipo else None,
                    'equipo_asociado_nombre': instance.equipo.nombre if instance.equipo else None,
                    'sede': instance.sede.id if instance.sede else None,
                    'sede_nombre': instance.sede.nombre if instance.sede else None,
                    'responsable': instance.responsable.id if instance.responsable else None,
                    'responsable_nombre': responsable_nombre,
                    'usuario_responsable_username': usuario_responsable_username,
                    'tipo_mantenimiento': instance.tipo_mantenimiento,
                    'estado_mantenimiento': instance.estado_mantenimiento,
                    'fecha_inicio': instance.fecha_inicio,
                    'fecha_finalizacion': instance.fecha_finalizacion,
                    'descripcion_problema': instance.descripcion_problema,
                    'acciones_realizadas': instance.acciones_realizadas,
                    'repuestos_utilizados': instance.repuestos_utilizados,
                    'notas': instance.notas,
                    'creado_en': instance.creado_en,
                    'actualizado_en': instance.actualizado_en,
                    'evidencias': evidencias_data,
                    'evidencia_finalizacion_url': evidencia_finalizacion_url,
                    'evidencia_finalizacion_filename': evidencia_finalizacion_filename
                }
                return data
            except Exception as e2:
                # Si aún falla, retornamos un error mínimo
                print(f"ERROR crítico al serializar mantenimiento {instance.id}: {str(e2)}")
                return {
                    'id': instance.id,
                    'error': f'Error al serializar mantenimiento: {str(e)}'
                }
class HistorialAccionMantenimientoSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    equipo_nombre = serializers.CharField(source='mantenimiento.equipo.nombre', read_only=True)
    mantenimiento_id = serializers.IntegerField(source='mantenimiento.id', read_only=True)
    sede_id = serializers.IntegerField(source='mantenimiento.sede.id', read_only=True)

    class Meta:
        model = HistorialAccionMantenimiento
        fields = ['id', 'mantenimiento_id', 'usuario', 'usuario_username', 'accion', 'detalle', 'fecha', 'equipo_nombre', 'sede_id']
