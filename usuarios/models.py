# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User
from sede.models import Sede
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True)
    cargo = models.CharField(max_length=100, blank=True, null=True) # Nuevo campo
    area = models.CharField(max_length=100, blank=True, null=True) # Nuevo campo
    rol = models.CharField(max_length=20, choices=[('ADMIN', 'Admin'), ('USUARIO', 'Usuario')], default='USUARIO') # Campo 'rol' restaurado

    def __str__(self):
        return f'{self.user.username} Profile'

# Señal para crear o actualizar el UserProfile automáticamente
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    # Para usuarios existentes, solo nos aseguramos de que el perfil exista si
    # por alguna razón no se creó. No lo guardamos para no sobrescribir datos.
    elif not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
