from django.contrib.auth.models import User
from rest_framework import serializers
from sede.models import Sede # Importado desde sede.models
from mantenimientos.models import Mantenimiento # Importado desde mantenimientos.models
from .models import Equipo, Periferico, Licencia, Pasisalvo, HistorialEquipo, HistorialMovimientoEquipo, ReporteIncidente
from .models import HistorialPeriferico
from usuarios.serializers import UserSerializer # Importar UserSerializer


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = '__all__'

class EquipoSerializer(serializers.ModelSerializer):
    # Campo para mostrar el nombre de la sede (solo lectura).
    sede_nombre = serializers.SerializerMethodField()

    def get_sede_nombre(self, obj):
        return obj.sede.nombre if obj.sede else None
    # Usar un serializador anidado para mostrar la información completa del usuario (solo lectura).
    usuario_asignado = serializers.SerializerMethodField()
    # Campo adicional para mostrar información del empleado asignado
    empleado_asignado_info = serializers.SerializerMethodField()
    # Campo para mostrar información del responsable de custodia temporal
    responsable_custodia_info = serializers.SerializerMethodField()
    # Campo para aceptar el ID del usuario al crear/actualizar un equipo (solo escritura).
    usuario_asignado_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    total_mantenimientos = serializers.SerializerMethodField()
    diagnostico_salud = serializers.SerializerMethodField()

    class Meta:
        model = Equipo
        fields = [
            'id', 'nombre', 'marca', 'modelo', 'serial', 'ram', 'rom',
            'sistema_operativo', 'procesador', 'antivirus', 'usuarios_sistema',
            'tipo_equipo', 'redes_conectadas',
            'estado_tecnico', 'estado_disponibilidad', 'sede', 'sede_nombre',
            'empleado_asignado', 'usuario_asignado', 'usuario_asignado_id', 'empleado_asignado_info',
            'responsable_custodia', 'responsable_custodia_info', 'fecha_recepcion_custodia', 'notas_custodia',
            'fecha_entrega_a_colaborador', 'fecha_recibido_satisfaccion',
            'responsable_entrega', 'nombre_jefe', 'cargo_jefe', 
            'firma_recibido_usuario', 'firma_recibido_jefe', 'firma_compromiso',
            'fecha_ultimo_mantenimiento', 'fecha_proximo_mantenimiento',
            'total_mantenimientos', 'diagnostico_salud',
            'notas', 'imagen', 'delete_imagen'
        ]
        read_only_fields = ['sede_nombre', 'usuario_asignado', 'empleado_asignado_info', 'responsable_custodia_info', 'total_mantenimientos', 'diagnostico_salud']
    
    delete_imagen = serializers.BooleanField(write_only=True, required=False)

    def create(self, validated_data):
        # Remover 'delete_imagen' si viene en los datos (no aplica al crear)
        validated_data.pop('delete_imagen', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        delete_imagen = validated_data.pop('delete_imagen', False)
        if delete_imagen and instance.imagen:
            instance.imagen.delete(save=False)
            instance.imagen = None
        return super().update(instance, validated_data)

    def get_total_mantenimientos(self, obj):
        return obj.historial_mantenimientos.filter(estado_mantenimiento='Finalizado').count()

    def get_diagnostico_salud(self, obj):
        count = obj.historial_mantenimientos.filter(estado_mantenimiento='Finalizado').count()
        if count <= 3:
            return {'rango': 'Óptimo', 'color': 'green', 'mensaje': 'Equipo en excelente estado técnico.'}
        elif count <= 6:
            return {'rango': 'Advertencia', 'color': 'yellow', 'mensaje': 'Uso frecuente detectado. Requiere monitoreo preventivo.'}
        else:
            return {'rango': 'Crítico', 'color': 'red', 'mensaje': '¡Riesgo alto! Alta tasa de fallos. Evaluar reemplazo preventivo.'}

    def get_usuario_asignado(self, obj):
        if obj.empleado_asignado and obj.empleado_asignado.user:
            return UserSerializer(obj.empleado_asignado.user).data
        return None

    def get_empleado_asignado_info(self, obj):
        if obj.empleado_asignado:
            return {
                'id': obj.empleado_asignado.id,
                'nombre': obj.empleado_asignado.nombre,
                'apellido': obj.empleado_asignado.apellido,
                'nombre_completo': f"{obj.empleado_asignado.nombre} {obj.empleado_asignado.apellido}",
                'cargo': obj.empleado_asignado.cargo,
                'area': obj.empleado_asignado.area,
                'tiene_user': obj.empleado_asignado.user is not None,
                'user_id': obj.empleado_asignado.user.id if obj.empleado_asignado.user else None
            }
        return None

    def get_responsable_custodia_info(self, obj):
        if obj.responsable_custodia:
            return {
                'id': obj.responsable_custodia.id,
                'nombre': obj.responsable_custodia.nombre,
                'apellido': obj.responsable_custodia.apellido,
                'nombre_completo': f"{obj.responsable_custodia.nombre} {obj.responsable_custodia.apellido}",
                'cargo': obj.responsable_custodia.cargo,
                'area': obj.responsable_custodia.area,
            }
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation


class MantenimientoSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)
    responsable_username = serializers.CharField(source='responsable.username', read_only=True, allow_null=True)
    sede_nombre = serializers.CharField(source='sede.nombre', read_only=True, allow_null=True)
    tipo_mantenimiento_nombre = serializers.CharField(source='get_tipo_mantenimiento_display', read_only=True)
    fecha_proximo_mantenimiento_equipo = serializers.DateField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Mantenimiento
        fields = [
            'id',
            'equipo',
            'equipo_nombre',
            'tipo_mantenimiento',
            'tipo_mantenimiento_nombre',
            'responsable',
            'responsable_username',
            'fecha_inicio',
            'fecha_finalizacion',
            'estado_mantenimiento',
            'descripcion_problema',
            'acciones_realizadas',
            'repuestos_utilizados',
            'sede',
            'sede_nombre',
            'notas',
            'evidencia',
            'fecha_proximo_mantenimiento_equipo',
        ]
        read_only_fields = ['equipo_nombre', 'responsable_username', 'sede_nombre', 'tipo_mantenimiento_nombre']


class PerifericoSerializer(serializers.ModelSerializer):
    empleado_asignado_info = serializers.SerializerMethodField()
    equipo_asociado_serial = serializers.CharField(source='equipo_asociado.serial', read_only=True, allow_null=True)
    sede_nombre = serializers.CharField(source='sede.nombre', read_only=True, allow_null=True)

    class Meta:
        model = Periferico
        fields = [
            'id', 'nombre', 'tipo', 'estado_tecnico', 'estado_disponibilidad',
            'empleado_asignado', 'empleado_asignado_info', 'equipo_asociado',
            'equipo_asociado_serial', 'sede', 'sede_nombre', 'fecha_entrega', 'notas'
        ]
        read_only_fields = ['empleado_asignado_info', 'equipo_asociado_serial', 'sede_nombre']

    def get_empleado_asignado_info(self, obj):
        if obj.empleado_asignado:
            return {
                'id': obj.empleado_asignado.id,
                'nombre': obj.empleado_asignado.nombre,
                'apellido': obj.empleado_asignado.apellido,
                'nombre_completo': f"{obj.empleado_asignado.nombre} {obj.empleado_asignado.apellido}",
                'cargo': obj.empleado_asignado.cargo,
                'area': obj.empleado_asignado.area,
            }
        return None

class LicenciaSerializer(serializers.ModelSerializer):
    equipo_asociado_info = serializers.SerializerMethodField()

    class Meta:
        model = Licencia
        fields = [
            'id', 'equipo_asociado', 'equipo_asociado_info', 'tipo_licencia',
            'tipo_activacion', 'clave', 'fecha_instalacion', 'fecha_vencimiento', 'estado', 'notas'
        ]
        read_only_fields = ['equipo_asociado_info']

    def get_equipo_asociado_info(self, obj):
        if obj.equipo_asociado:
            return {
                'id': obj.equipo_asociado.id,
                'nombre': obj.equipo_asociado.nombre,
                'serial': obj.equipo_asociado.serial,
            }
        return None

class PasisalvoSerializer(serializers.ModelSerializer):
    colaborador_info = serializers.SerializerMethodField()
    recibido_por_info = serializers.SerializerMethodField()
    generado_por_username = serializers.CharField(source='generado_por.username', read_only=True, allow_null=True)

    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Pasisalvo
        fields = [
            'id', 'colaborador', 'colaborador_info', 'fecha_generacion', 
            'estado', 'detalles_pendientes', 'generado_por', 'generado_por_username', 
            'recibido_por', 'recibido_por_info', 'firma_recibido', 'pdf_url', 'pdf_archivo'
        ]

        read_only_fields = ['fecha_generacion', 'generado_por_username', 'colaborador_info', 'recibido_por_info']

    def get_pdf_url(self, obj):
        if obj.pdf_archivo:
            return obj.pdf_archivo.url
        return None

    def get_colaborador_info(self, obj):
        if obj.colaborador:
            return {
                'id': obj.colaborador.id,
                'nombre_completo': f"{obj.colaborador.nombre} {obj.colaborador.apellido}",
                'cedula': obj.colaborador.cedula,
                'cargo': obj.colaborador.cargo,
                'area': obj.colaborador.area,
            }
        return None

    def get_recibido_por_info(self, obj):
        if obj.recibido_por:
            return {
                'id': obj.recibido_por.id,
                'nombre_completo': f"{obj.recibido_por.nombre} {obj.recibido_por.apellido}",
                'cargo': obj.recibido_por.cargo,
                'area': obj.recibido_por.area,
            }
        return None

class HistorialPerifericoSerializer(serializers.ModelSerializer):
    periferico_nombre = serializers.CharField(read_only=True)
    empleado_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = HistorialPeriferico
        fields = '__all__'

    def get_empleado_nombre(self, obj):
        if obj.empleado_asignado:
            return f"{obj.empleado_asignado.nombre} {obj.empleado_asignado.apellido}"
        return "Sin asignar"

class HistorialEquipoSerializer(serializers.ModelSerializer):
    """
    Serializer para el historial de cambios de un equipo.
    """
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True, allow_null=True)

    class Meta:
        model = HistorialEquipo
        fields = [
            'id',
            'fecha_cambio',
            'campo_modificado',
            'valor_anterior',
            'valor_nuevo',
            'tipo_accion',
            'usuario_nombre',
        ]

class HistorialMovimientoEquipoSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(read_only=True)
    equipo_serial = serializers.CharField(read_only=True)
    empleado_nombre = serializers.SerializerMethodField()
    # NOTA: responsable_custodia_info fue eliminado — el modelo HistorialMovimientoEquipo
    # no tiene ese campo, lo cual causaba un AttributeError (500) al listar movimientos.
    
    class Meta:
        model = HistorialMovimientoEquipo
        fields = '__all__'

    def get_empleado_nombre(self, obj):
        if obj.empleado_asignado:
            return f"{obj.empleado_asignado.nombre} {obj.empleado_asignado.apellido}"
        return "Sin asignar"


class ReporteIncidenteSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo ReporteIncidente.
    El frontend lo consume en GET /api/incidentes/?equipo=<id> y POST /api/incidentes/
    """
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)
    creado_por_username = serializers.CharField(source='creado_por.username', read_only=True, allow_null=True)

    class Meta:
        model = ReporteIncidente
        fields = [
            'id', 'equipo', 'equipo_nombre', 'empleado',
            'tipo_incidente', 'descripcion', 'fecha_incidente',
            'resolucion', 'equipo_nuevo', 'evidencia_foto',
            'costo_estimado', 'creado_en', 'creado_por', 'creado_por_username'
        ]
        read_only_fields = ['fecha_incidente', 'creado_en', 'creado_por', 'creado_por_username', 'equipo_nombre']
