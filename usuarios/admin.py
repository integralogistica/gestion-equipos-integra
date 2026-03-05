from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile
from sede.models import Sede

# (Comentado/eliminado) UserProfileInline para probar un UserProfileAdmin directo
# class UserProfileInline(admin.StackedInline):
#     model = UserProfile
#     can_delete = False
#     verbose_name_plural = 'Perfil (Sede)'
#     fk_name = 'user'
#
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if db_field.name == "sede":
#             kwargs["queryset"] = Sede.objects.all()
#         return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Nueva clase UserProfileAdmin para registrar UserProfile directamente
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'sede', 'cargo', 'area', 'rol')
    search_fields = ('user__username', 'sede__nombre', 'cargo', 'area', 'rol')
    list_filter = ('sede', 'rol')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "sede":
            # Asegúrate de que el queryset incluye todas las sedes
            kwargs["queryset"] = Sede.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# 3. Crear una nueva clase de administrador de usuarios que incluya el inline
class CustomUserAdmin(UserAdmin):
    # Ya no incluimos UserProfileInline aquí
    def get_inlines(self, request, obj=None):
        return () # No inlines para el UserAdmin por ahora

    # Opcional: para mostrar la sede en la lista de usuarios
    def get_sede(self, instance):
        return instance.profile.sede.nombre if hasattr(instance, 'profile') and instance.profile.sede else 'N/A'
    get_sede.short_description = 'Sede'

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_sede')
    list_select_related = ('profile__sede', )

# 4. Anular el registro del UserAdmin por defecto y registrar el nuestro
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)