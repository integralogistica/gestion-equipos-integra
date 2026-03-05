from django.contrib import admin

from mantenimientos.models import Mantenimiento
from .models import Equipo, Periferico, Licencia, Pasisalvo, HistorialEquipo


class HistorialEquipoInline(admin.TabularInline):
    model = HistorialEquipo
    extra = 0
    readonly_fields = ('fecha_cambio', 'usuario', 'campo_modificado', 'valor_anterior', 'valor_nuevo', 'tipo_accion')
    can_delete = False
    verbose_name_plural = 'Historial de Cambios'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

class EquipoAdmin(admin.ModelAdmin):
    inlines = [HistorialEquipoInline]
    list_display = ('nombre', 'serial', 'marca', 'modelo', 'sede', 'empleado_asignado', 'estado_tecnico', 'estado_disponibilidad')
    list_filter = ('sede', 'estado_tecnico', 'estado_disponibilidad', 'marca')
    search_fields = ('nombre', 'serial', 'empleado_asignado__nombre')

# Register your models here.


admin.site.register(Equipo, EquipoAdmin)
admin.site.register(Mantenimiento)
admin.site.register(Periferico)
admin.site.register(Licencia)
admin.site.register(Pasisalvo)
