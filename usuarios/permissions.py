from rest_framework.permissions import BasePermission
from .models import UserProfile

class IsAdminUser(BasePermission):
    """
    Permiso que solo permite el acceso a usuarios con rol de ADMIN.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.rol == 'ADMIN'
        )

class IsManagerUser(BasePermission):
    """
    Permiso que solo permite el acceso a usuarios con rol de MANAGER.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.rol == 'MANAGER'
        )

class IsTechnicianUser(BasePermission):
    """
    Permiso que solo permite el acceso a usuarios con rol de TECHNICIAN.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.rol == 'TECHNICIAN'
        )

class IsManagerOrAdmin(BasePermission):
    """
    Permiso para roles de MANAGER o ADMIN.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.rol in ['ADMIN', 'MANAGER']
        )

class IsAdminOrOwnerBySede(BasePermission):
    """
    Permiso personalizado para permitir el acceso a administradores
    o a usuarios si el objeto pertenece a su misma sede.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if not user.is_authenticated:
            return False

        try:
            user_profile = user.profile
            if user.is_staff or user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN'):
                return True
        except UserProfile.DoesNotExist:
            if user.is_staff or user.is_superuser:
                return True
            return False

        user_sede = getattr(user_profile, 'sede', None)
        if not user_sede:
            return False

        obj_sede = None
        if hasattr(obj, 'sede'):
            obj_sede = obj.sede
        elif hasattr(obj, 'equipo_asociado') and obj.equipo_asociado:
            obj_sede = obj.equipo_asociado.sede
        elif hasattr(obj, 'equipo') and obj.equipo:
            obj_sede = obj.equipo.sede
        elif hasattr(obj, 'user') and hasattr(obj.user, 'profile') and obj.user.profile:
            obj_sede = obj.user.profile.sede
        elif type(obj).__name__ == 'Sede':
            obj_sede = obj
        
        return obj_sede is not None and obj_sede == user_sede

class IsAdminOrSelf(BasePermission):
    """
    Permiso para permitir el acceso solo a administradores o al propio usuario.
    """
    def has_object_permission(self, request, view, obj):
        is_owner = False
        if hasattr(obj, 'user'): # Para UserProfile
            is_owner = obj.user == request.user
        elif type(obj).__name__ == 'User': # Para el modelo User directamente
            is_owner = obj == request.user

        is_admin = False
        try:
            user_profile = request.user.profile
            is_admin = request.user.is_staff or request.user.is_superuser or (hasattr(user_profile, 'rol') and user_profile.rol == 'ADMIN')
        except UserProfile.DoesNotExist:
            is_admin = request.user.is_staff or request.user.is_superuser
            
        return is_owner or is_admin
