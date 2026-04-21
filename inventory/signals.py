from django.utils import timezone
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from .models import Equipo, HistorialEquipo, Periferico, HistorialPeriferico, HistorialMovimientoEquipo
from .middleware import get_current_user

@receiver(pre_save, sender=Equipo)
def cache_old_equipo_instance(sender, instance, **kwargs):
    """
    On pre_save, cache the old instance of the Equipo model if it exists.
    """
    if instance.pk:
        try:
            instance._old_instance = Equipo.objects.get(pk=instance.pk)
        except Equipo.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None


@receiver(post_save, sender=Equipo)
def log_equipo_changes(sender, instance, created, **kwargs):
    """
    On post_save, compare the new instance with the cached old one and log changes.
    """
    user = get_current_user()

    old_instance = getattr(instance, '_old_instance', None)
    
    if created:
        # For a created instance, we can log the initial state of all fields.
        for field in instance._meta.fields:
            if field.name == 'id':
                continue
            
            new_value = getattr(instance, field.name)
            if new_value not in [None, '']:
                HistorialEquipo.objects.create(
                    equipo=instance,
                    usuario=user,
                    campo_modificado=field.verbose_name,
                    valor_anterior="",
                    valor_nuevo=str(new_value),
                    tipo_accion='CREADO'
                )
    elif old_instance is not None:
        # For an updated instance, we compare fields and log what changed.
        for field in instance._meta.fields:
            old_value = getattr(old_instance, field.name)
            new_value = getattr(instance, field.name)

            if field.is_relation and old_value != new_value:
                old_val_str = str(old_value) if old_value else ""
                new_val_str = str(new_value) if new_value else ""

                if old_val_str != new_val_str:
                    HistorialEquipo.objects.create(
                        equipo=instance,
                        usuario=user,
                        campo_modificado=field.verbose_name,
                        valor_anterior=old_val_str,
                        valor_nuevo=new_val_str,
                        tipo_accion='ACTUALIZADO'
                    )
            elif not field.is_relation and old_value != new_value:
                HistorialEquipo.objects.create(
                    equipo=instance,
                    usuario=user,
                    campo_modificado=field.verbose_name,
                    valor_anterior=str(old_value),
                    valor_nuevo=str(new_value),
                    tipo_accion='ACTUALIZADO'
                )

@receiver(pre_save, sender=Periferico)
def cache_old_periferico_instance(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = Periferico.objects.get(pk=instance.pk)
        except Periferico.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None


@receiver(post_save, sender=Periferico)
def log_periferico_assignment(sender, instance, created, **kwargs):
    old_instance = getattr(instance, '_old_instance', None)
    
    # Si se acaba de asignar (antes era None y ahora tiene empleado)
    if (not old_instance or not old_instance.empleado_asignado) and instance.empleado_asignado:
        HistorialPeriferico.objects.create(
            periferico=instance,
            empleado_asignado=instance.empleado_asignado,
            equipo_asociado=instance.equipo_asociado
        )
    
    # Si se cambió de un empleado a otro
    elif old_instance and old_instance.empleado_asignado and instance.empleado_asignado and old_instance.empleado_asignado != instance.empleado_asignado:
        # Marcar devolución del anterior
        HistorialPeriferico.objects.filter(
            periferico=instance, 
            empleado_asignado=old_instance.empleado_asignado,
            fecha_devolucion__isnull=True
        ).update(fecha_devolucion=instance.fecha_entrega or timezone.now(), observacion_devolucion="Reasignación automática")
        
        HistorialPeriferico.objects.create(
            periferico=instance,
            empleado_asignado=instance.empleado_asignado,
            equipo_asociado=instance.equipo_asociado
        )
    
    # Si se devolvió (antes tenía empleado y ahora no)
    elif old_instance and old_instance.empleado_asignado and not instance.empleado_asignado:
        HistorialPeriferico.objects.filter(
            periferico=instance, 
            empleado_asignado=old_instance.empleado_asignado,
            fecha_devolucion__isnull=True
        ).update(fecha_devolucion=timezone.now(), observacion_devolucion="Devolución automática")

@receiver(pre_delete, sender=Periferico)
def log_periferico_baja(sender, instance, **kwargs):
    # Si estaba asignado a alguien, marcamos la devolución
    if instance.empleado_asignado:
        HistorialPeriferico.objects.filter(
            periferico=instance, 
            empleado_asignado=instance.empleado_asignado,
            fecha_devolucion__isnull=True
        ).update(fecha_devolucion=timezone.now(), observacion_devolucion="Devolución por baja del elemento")
    
    # Creamos un registro final de baja
    HistorialPeriferico.objects.create(
        periferico=instance,
        periferico_nombre=instance.nombre,
        es_baja=True,
        fecha_baja=timezone.now(),
        observacion_devolucion="SISTEMA: PERIFÉRICO DADO DE BAJA"
    )

@receiver(post_save, sender=Equipo)
def log_equipo_movement(sender, instance, created, **kwargs):
    old_instance = getattr(instance, '_old_instance', None)
    
    # 1. Caso: Nuevo equipo con empleado asignado
    if created and instance.empleado_asignado:
        HistorialMovimientoEquipo.objects.create(
            equipo=instance,
            empleado_asignado=instance.empleado_asignado
        )
    
    # 2. Caso: Actualización de equipo
    elif old_instance:
        # Cambio de empleado (Asignación o Reasignación o Devolución)
        if instance.empleado_asignado_id != old_instance.empleado_asignado_id:
            # Si había un empleado anterior, cerrar su registro de movimiento (Devolución)
            if old_instance.empleado_asignado:
                historial_activo = HistorialMovimientoEquipo.objects.filter(
                    equipo=instance,
                    empleado_asignado=old_instance.empleado_asignado,
                    fecha_devolucion__isnull=True,
                    es_baja=False
                ).first()
                
                if historial_activo:
                    historial_activo.fecha_devolucion = timezone.now()
                    historial_activo.observacion_devolucion = instance.notas_custodia or "Devolución recibida satisfactoriamente"
                    
                    # CAPTURAR RESPONSABLE DE CUSTODIA (NUEVO)
                    historial_activo.responsable_custodia = instance.responsable_custodia
                    
                    # CAPTURAR FOTO DE DEVOLUCIÓN
                    historial_activo.ram_devolucion = instance.ram
                    historial_activo.rom_devolucion = instance.rom
                    historial_activo.so_devolucion = instance.sistema_operativo
                    historial_activo.procesador_devolucion = instance.procesador
                    historial_activo.estado_fisico_devolucion = instance.estado_fisico
                    
                    historial_activo.save()
            
            # Si hay un nuevo empleado, crear nuevo registro (Asignación)
            if instance.empleado_asignado:
                HistorialMovimientoEquipo.objects.create(
                    equipo=instance,
                    empleado_asignado=instance.empleado_asignado
                )
        
        # Caso: El equipo se da de baja
        if old_instance.activo and not instance.activo:
            # Si estaba asignado, cerrar la asignación
            if instance.empleado_asignado:
                HistorialMovimientoEquipo.objects.filter(
                    equipo=instance,
                    empleado_asignado=instance.empleado_asignado,
                    fecha_devolucion__isnull=True,
                    es_baja=False
                ).update(
                    fecha_devolucion=timezone.now(),
                    observacion_devolucion="Devolución por baja del equipo"
                )
            
            # Crear registro de baja
            HistorialMovimientoEquipo.objects.create(
                equipo=instance,
                es_baja=True,
                fecha_baja=timezone.now(),
                observacion_devolucion="SISTEMA: EQUIPO DADO DE BAJA"
            )
