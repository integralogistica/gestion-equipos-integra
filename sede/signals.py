from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import Sede, HistorialSede
from inventory.middleware import get_current_user

@receiver(pre_save, sender=Sede)
def cache_old_sede_instance(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = Sede.objects.get(pk=instance.pk)
        except Sede.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None


@receiver(post_save, sender=Sede)
def log_sede_changes(sender, instance, created, **kwargs):
    user = get_current_user()
    sede_str = str(instance)
    old_instance = getattr(instance, '_old_instance', None)
    
    if created:
        for field in instance._meta.fields:
            if field.name == 'id':
                continue
            
            new_value = getattr(instance, field.name)
            if new_value not in [None, '']:
                HistorialSede.objects.create(
                    sede=instance,
                    sede_str=sede_str,
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

            if old_value != new_value:
                HistorialSede.objects.create(
                    sede=instance,
                    sede_str=sede_str,
                    usuario=user,
                    campo_modificado=field.verbose_name,
                    valor_anterior=str(old_value),
                    valor_nuevo=str(new_value),
                    tipo_accion='ACTUALIZADO'
                )

@receiver(post_delete, sender=Sede)
def log_sede_deletion(sender, instance, **kwargs):
    user = get_current_user()
    sede_str = str(instance)
    
    HistorialSede.objects.create(
        sede=None,
        sede_str=sede_str,
        usuario=user,
        campo_modificado="Registro completo",
        valor_anterior=f"La sede '{sede_str}' (ID: {instance.id}) fue eliminada.",
        valor_nuevo="",
        tipo_accion='ELIMINADO'
    )
