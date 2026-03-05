from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import Empleado, HistorialEmpleado
from inventory.middleware import get_current_user

@receiver(pre_save, sender=Empleado)
def cache_old_empleado_instance(sender, instance, **kwargs):
    """
    En pre_save, guarda en caché la instancia antigua del modelo Empleado si existe.
    """
    if instance.pk:
        try:
            instance._old_instance = Empleado.objects.get(pk=instance.pk)
        except Empleado.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None


@receiver(post_save, sender=Empleado)
def log_empleado_changes(sender, instance, created, **kwargs):
    """
    En post_save, compara la nueva instancia con la antigua en caché y registra los cambios.
    """
    user = get_current_user()
    empleado_str = str(instance)
    old_instance = getattr(instance, '_old_instance', None)
    
    if created:
        for field in instance._meta.fields:
            if field.name == 'id':
                continue
            
            new_value = getattr(instance, field.name)
            if new_value not in [None, '']:
                HistorialEmpleado.objects.create(
                    empleado=instance,
                    empleado_str=empleado_str,
                    usuario=user,
                    campo_modificado=field.verbose_name,
                    valor_anterior="",
                    valor_nuevo=str(new_value),
                    tipo_accion='CREADO'
                )
    elif old_instance is not None:
        for field in instance._meta.fields:
            old_value = getattr(old_instance, field.name)
            new_value = getattr(instance, field.name)

            # Para campos de relación, comparar los IDs si es posible
            if field.is_relation:
                old_value_id = getattr(old_instance, f'{field.name}_id', old_value)
                new_value_id = getattr(instance, f'{field.name}_id', new_value)
                if old_value_id != new_value_id:
                    old_val_str = str(old_value) if old_value else "Ninguno"
                    new_val_str = str(new_value) if new_value else "Ninguno"
                    HistorialEmpleado.objects.create(
                        empleado=instance,
                        empleado_str=empleado_str,
                        usuario=user,
                        campo_modificado=field.verbose_name,
                        valor_anterior=old_val_str,
                        valor_nuevo=new_val_str,
                        tipo_accion='ACTUALIZADO'
                    )
            # Para otros campos, comparar directamente los valores
            elif old_value != new_value:
                HistorialEmpleado.objects.create(
                    empleado=instance,
                    empleado_str=empleado_str,
                    usuario=user,
                    campo_modificado=field.verbose_name,
                    valor_anterior=str(old_value),
                    valor_nuevo=str(new_value),
                    tipo_accion='ACTUALIZADO'
                )

@receiver(post_delete, sender=Empleado)
def log_empleado_deletion(sender, instance, **kwargs):
    """
    En post_delete, registra la eliminación de la instancia de Empleado.
    """
    user = get_current_user()
    empleado_str = str(instance)
    
    HistorialEmpleado.objects.create(
        empleado=None,
        empleado_str=empleado_str,
        usuario=user,
        campo_modificado="Registro completo",
        valor_anterior=f"El empleado '{empleado_str}' (ID: {instance.id}) fue eliminado.",
        valor_nuevo="",
        tipo_accion='ELIMINADO'
    )
