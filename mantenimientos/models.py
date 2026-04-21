from django.db import models
from django.contrib.auth.models import User
from inventory.models import Equipo # Asumo que el modelo Equipo está en la app 'inventory'
from  sede.models import Sede
from datetime import date

class Mantenimiento(models.Model):
    """
    Modelo para registrar los mantenimientos realizados a los equipos.
    """
    TIPO_MANTENIMIENTO_CHOICES = [
        ('Preventivo', 'Preventivo'),
        ('Correctivo', 'Correctivo'),
    ]

    ESTADO_MANTENIMIENTO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En proceso', 'En proceso'),
        ('Finalizado', 'Finalizado'),
        ('Cancelado', 'Cancelado'),
    ]

    # Relaciones clave
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='historial_mantenimientos')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="Técnico que realiza el mantenimiento")

    # Campos del mantenimiento
    tipo_mantenimiento = models.CharField(max_length=50, choices=TIPO_MANTENIMIENTO_CHOICES)
    estado_mantenimiento = models.CharField(max_length=50, choices=ESTADO_MANTENIMIENTO_CHOICES, default='Pendiente')
    
    # Fechas
    fecha_inicio = models.DateField(default=date.today)
    fecha_finalizacion = models.DateField(null=True, blank=True, help_text="Fecha límite estimada")
    fecha_real_finalizacion = models.DateField(null=True, blank=True, help_text="Fecha en la que realmente se marcó como finalizado")

    # Descripción y resultados
    descripcion_problema = models.TextField(blank=True, help_text="Qué problema presentaba el equipo")
    acciones_realizadas = models.TextField(blank=True, help_text="Qué se hizo durante el mantenimiento")
    repuestos_utilizados = models.TextField(blank=True)
    
    # Evidencia y notas
    notas = models.TextField(blank=True)
    evidencia_finalizacion = models.FileField(upload_to='evidencias_finalizacion/', blank=True, null=True, help_text="Evidencia de finalización del mantenimiento")

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    @property
    def fuera_de_fecha(self):
        """
        Determina si el mantenimiento se finalizó después de la fecha límite
        o si ya está vencido pero sigue pendiente.
        """
        if self.estado_mantenimiento == 'Finalizado':
            if self.fecha_real_finalizacion and self.fecha_finalizacion:
                return self.fecha_real_finalizacion > self.fecha_finalizacion
            return False
        
        # Si sigue pendiente y ya pasó la fecha límite
        today = date.today()
        if self.estado_mantenimiento in ['Pendiente', 'En proceso'] and self.fecha_finalizacion:
            return today > self.fecha_finalizacion
        
        return False

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['equipo'],
                condition=models.Q(estado_mantenimiento__in=['Pendiente', 'En proceso']),
                name='unique_pending_or_in_process_maintenance_per_equipo'
            )
        ]

    def __str__(self):
        return f"{self.tipo_mantenimiento} en {self.equipo.nombre} - {self.estado_mantenimiento}"

class EvidenciaMantenimiento(models.Model):
    """
    Modelo para almacenar las evidencias (archivos/imágenes) de un mantenimiento.
    """
    mantenimiento = models.ForeignKey(Mantenimiento, on_delete=models.CASCADE, related_name='evidencias')
    archivo = models.FileField(upload_to='evidencias_mantenimiento/')

    def __str__(self):
        return f"Evidencia para {self.mantenimiento.id}"
class HistorialAccionMantenimiento(models.Model):
    """
    Modelo para registrar cada acción realizada sobre un mantenimiento.
    """
    mantenimiento = models.ForeignKey(Mantenimiento, on_delete=models.CASCADE, related_name='acciones_historial')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=100) # Ej: "Inició proceso", "Finalizó mantenimiento"
    detalle = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Historial de Acción de Mantenimiento"
        verbose_name_plural = "Historiales de Acciones de Mantenimiento"

    def __str__(self):
        return f"{self.accion} - {self.mantenimiento.equipo.nombre} ({self.fecha})"
