from django.db import models
from django.conf import settings
from empleados.models import Empleado
from sede.models import Sede
from django.contrib.auth.models import User
from datetime import date

class Equipo(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Equipo")
    marca = models.CharField(max_length=50, verbose_name="Marca")
    modelo = models.CharField(max_length=50, verbose_name="Modelo")
    serial = models.CharField(max_length=50, unique=True, verbose_name="Serial")
    ram = models.CharField(max_length=20, blank=True, null=True, verbose_name="RAM")
    rom = models.CharField(max_length=20, blank=True, null=True, verbose_name="Almacenamiento")
    sistema_operativo = models.CharField(max_length=100, blank=True, null=True)
    procesador = models.CharField(max_length=100, blank=True, null=True)
    antivirus = models.CharField(max_length=100, blank=True, null=True)
    usuarios_sistema = models.TextField(blank=True, null=True)
    tipo_equipo = models.CharField(max_length=50, default='Laptop')
    redes_conectadas = models.TextField(blank=True, null=True)
    estado_tecnico = models.CharField(max_length=50, default='Nuevo')
    estado_disponibilidad = models.CharField(max_length=50, default='Disponible')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True)
    activo = models.BooleanField(default=True)
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos_asignados')
    fecha_entrega_a_colaborador = models.DateField(null=True, blank=True)
    responsable_custodia = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='custodias')
    fecha_recepcion_custodia = models.DateTimeField(null=True, blank=True)
    notas_custodia = models.TextField(blank=True, null=True)
    fecha_recibido_satisfaccion = models.DateTimeField(null=True, blank=True)
    responsable_entrega = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    firma_recibido_usuario = models.TextField(blank=True, null=True)
    nombre_jefe = models.CharField(max_length=150, blank=True, null=True)
    cargo_jefe = models.CharField(max_length=100, blank=True, null=True)
    firma_recibido_jefe = models.TextField(blank=True, null=True)
    firma_compromiso = models.TextField(blank=True, null=True)
    fecha_ultimo_mantenimiento = models.DateField(null=True, blank=True)
    fecha_proximo_mantenimiento = models.DateField(null=True, blank=True)
    estado_fisico = models.TextField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='equipos_fotos/', null=True, blank=True)

    def __str__(self): return f"{self.nombre} - {self.serial}"

class Periferico(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    tipo_otro = models.CharField(max_length=100, blank=True, null=True)
    estado_tecnico = models.CharField(max_length=50, default='Funcional')
    estado_disponibilidad = models.CharField(max_length=50, default='Disponible')
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    equipo_asociado = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='perifericos')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True, null=True)

class Licencia(models.Model):
    equipo_asociado = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='licencias')
    tipo_licencia = models.CharField(max_length=50)
    tipo_licencia_otro = models.CharField(max_length=100, blank=True, null=True)
    tipo_activacion = models.CharField(max_length=50)
    clave = models.CharField(max_length=255, blank=True, null=True)
    fecha_instalacion = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=50, default='Activa')
    notas = models.TextField(blank=True, null=True)

class Pasisalvo(models.Model):
    colaborador = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50)
    pdf_archivo = models.FileField(upload_to='pasisalvos/', null=True, blank=True)

class HistorialPeriferico(models.Model):
    periferico = models.ForeignKey(Periferico, on_delete=models.SET_NULL, null=True, blank=True)
    periferico_nombre = models.CharField(max_length=200, null=True, blank=True)
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

class HistorialEquipo(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='historial_cambios')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    campo_modificado = models.CharField(max_length=100)
    valor_anterior = models.TextField(null=True, blank=True)
    valor_nuevo = models.TextField(null=True, blank=True)
    tipo_accion = models.CharField(max_length=20)

class HistorialMovimientoEquipo(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='historial_movimientos')
    equipo_nombre = models.CharField(max_length=200, null=True, blank=True)
    equipo_serial = models.CharField(max_length=100, null=True, blank=True)
    ram_entrega = models.CharField(max_length=20, blank=True, null=True)
    ram_devolucion = models.CharField(max_length=20, blank=True, null=True)
    rom_entrega = models.CharField(max_length=20, blank=True, null=True)
    rom_devolucion = models.CharField(max_length=20, blank=True, null=True)
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    responsable_custodia = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='custodias_recibidas')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_devolucion = models.DateTimeField(null=True, blank=True)

class ReporteIncidente(models.Model):
    TIPO_INCIDENTE_CHOICES = [
        ('Caída / Golpe', 'Caída / Golpe'),
        ('Derrame de Líquido', 'Derrame de Líquido'),
        ('Robo / Pérdida', 'Robo / Pérdida'),
        ('Falla Técnica Grave', 'Falla Técnica Grave'),
        ('Desgaste Natural', 'Desgaste Natural'),
        ('Uso Indebido', 'Uso Indebido'),
        ('Otro', 'Otro'),
    ]
    RESOLUCION_CHOICES = [
        ('Reparación Interna', 'Reparación Interna'),
        ('Garantía Fabricante', 'Garantía Fabricante'),
        ('Baja Total - Reposición', 'Baja Total - Reposición'),
        ('Cargo a Colaborador', 'Cargo a Colaborador'),
        ('Cerrado sin Acción', 'Cerrado sin Acción'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='incidentes')
    empleado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_incidente = models.CharField(max_length=50, choices=TIPO_INCIDENTE_CHOICES)
    descripcion = models.TextField()
    fecha_incidente = models.DateField(default=date.today)
    resolucion = models.CharField(max_length=50, choices=RESOLUCION_CHOICES, default='Reparación Interna')
    equipo_nuevo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='reposicion_de')
    evidencia_foto = models.ImageField(upload_to='incidentes_fotos/', null=True, blank=True)
    costo_estimado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    creado_en = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Reporte de Incidente"
        verbose_name_plural = "Reportes de Incidentes"
        ordering = ['-fecha_incidente']

    def __str__(self):
        return f"Incidente {self.tipo_incidente} - {self.equipo.nombre}"
