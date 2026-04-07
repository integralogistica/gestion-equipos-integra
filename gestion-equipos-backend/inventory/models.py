from django.db import models
from django.conf import settings
from empleados.models import Empleado
from sede.models import Sede
from django.contrib.auth.models import User
from datetime import date

# Nota: El modelo Equipo es el corazón del sistema.
class Equipo(models.Model):
    # --- SECCIÓN: Descripción del Equipo ---
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Equipo")
    marca = models.CharField(max_length=50, verbose_name="Marca")
    modelo = models.CharField(max_length=50, verbose_name="Modelo")
    serial = models.CharField(max_length=50, unique=True, verbose_name="Serial")
    ram = models.CharField(max_length=20, blank=True, null=True, verbose_name="Memoria RAM")
    rom = models.CharField(max_length=20, blank=True, null=True, verbose_name="Almacenamiento (ROM)")
    
    # Nuevos campos de descripción detallada
    sistema_operativo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Sistema Operativo")
    procesador = models.CharField(max_length=100, blank=True, null=True, verbose_name="Procesador")
    antivirus = models.CharField(max_length=100, blank=True, null=True, verbose_name="Antivirus Instalado")
    usuarios_sistema = models.TextField(blank=True, null=True, verbose_name="Usuarios del Sistema Operativo")
    
    TIPO_EQUIPO_CHOICES = [
        ('Laptop', 'Laptop'),
        ('Desktop', 'Desktop'),
        ('Servidor', 'Servidor'),
        ('Tablet', 'Tablet'),
        ('Movil', 'Movil'),
        ('Otro', 'Otro'),
    ]
    tipo_equipo = models.CharField(max_length=50, choices=TIPO_EQUIPO_CHOICES, default='Desktop', verbose_name="Tipo de Equipo")
    redes_conectadas = models.TextField(blank=True, null=True, verbose_name="Redes Conectadas")
    
    # --- SECCIÓN: Estado y Ubicación ---
    ESTADO_TECNICO_OPCIONES = [
        ('Nuevo', 'Nuevo'), 
        ('Reacondicionado', 'Reacondicionado'),
        ('Usado - Excelente', 'Usado - Excelente'),
        ('Usado - Regular', 'Usado - Regular'),
        ('En Obsolescencia', 'En Obsolescencia'),
    ]
    estado_tecnico = models.CharField(max_length=50, choices=ESTADO_TECNICO_OPCIONES, default='Nuevo', verbose_name="Estado Técnico")
    
    ESTADO_DISPONIBILIDAD_CHOICES = [
        ('Disponible', 'Disponible'), 
        ('Asignado', 'Asignado'), 
        ('Reservado', 'Reservado'), 
        ('No disponible por daño', 'No disponible por daño'), 
        ('No disponible por mantenimiento', 'No disponible por mantenimiento')
    ]
    estado_disponibilidad = models.CharField(max_length=50, choices=ESTADO_DISPONIBILIDAD_CHOICES, default='Disponible', verbose_name="Estado de Disponibilidad")
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sede")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    # --- SECCIÓN: A Cargo de ---
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos_asignados', verbose_name="Empleado Asignado")
    fecha_entrega_a_colaborador = models.DateField(null=True, blank=True, verbose_name="Fecha de Entrega a Colaborador")
    
    # --- SECCIÓN: Custodia Temporal ---
    responsable_custodia = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos_bajo_custodia', verbose_name="Responsable de Custodia Temporal")
    fecha_recepcion_custodia = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Recepción en Custodia")
    notas_custodia = models.TextField(blank=True, null=True, verbose_name="Notas de Custodia")
    
    # --- SECCIÓN: Recibido a Satisfacción ---
    fecha_recibido_satisfaccion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha y Hora de Recibo")
    responsable_entrega = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos_entregados', verbose_name="Responsable de la Entrega (TI)")
    firma_recibido_usuario = models.TextField(blank=True, null=True, verbose_name="Firma de Recibido del Colaborador")

    # --- SECCIÓN: Datos de Jefe Inmediato ---
    nombre_jefe = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nombre del Jefe Inmediato")
    cargo_jefe = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo del Jefe Inmediato")
    firma_recibido_jefe = models.TextField(blank=True, null=True, verbose_name="Firma de Recibido del Jefe")

    # --- SECCIÓN: Compromiso y Observaciones ---
    firma_compromiso = models.TextField(blank=True, null=True, verbose_name="Firma de Compromiso")
    
    # --- SECCIÓN: Fechas de Mantenimiento ---
    fecha_ultimo_mantenimiento = models.DateField(null=True, blank=True, verbose_name="Fecha del Último Mantenimiento")
    fecha_proximo_mantenimiento = models.DateField(null=True, blank=True, verbose_name="Fecha del Próximo Mantenimiento")

    # --- Notas e Imagen ---
    estado_fisico = models.TextField(blank=True, null=True, verbose_name="Estado Físico Actual")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas Internas (TI)")
    imagen = models.ImageField(upload_to='equipos_fotos/', null=True, blank=True, verbose_name="Fotografía del Equipo")

    def __str__(self):
        return f"{self.nombre} - {self.serial}"

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"


class Periferico(models.Model):
    TIPO_PERIFERICO_CHOICES = [
        ('Mouse', 'Mouse'),
        ('Teclado', 'Teclado'),
        ('Base', 'Base'),
        ('Cargador', 'Cargador'),
        ('Monitor', 'Monitor'),
        ('Auriculares', 'Auriculares'),
        ('Otro', 'Otro'),
    ]
    ESTADO_TECNICO_CHOICES = [
        ('Funcional', 'Funcional'),
        ('Con fallas', 'Con fallas'),
        ('Dañado', 'Dañado'),
    ]
    ESTADO_DISPONIBILIDAD_CHOICES = [
        ('Disponible', 'Disponible'),
        ('Asignado', 'Asignado'),
        ('Devuelto', 'Devuelto'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, choices=TIPO_PERIFERICO_CHOICES)
    tipo_otro = models.CharField(max_length=100, blank=True, null=True, verbose_name="¿Cuál otro periférico?")
    estado_tecnico = models.CharField(max_length=50, choices=ESTADO_TECNICO_CHOICES, default='Funcional')
    estado_disponibilidad = models.CharField(max_length=50, choices=ESTADO_DISPONIBILIDAD_CHOICES, default='Disponible')
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    equipo_asociado = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='perifericos')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name='perifericos')
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"


class Licencia(models.Model):
    TIPO_LICENCIA_CHOICES = [
        ('Sistema Operativo', 'Sistema Operativo'),
        ('Office', 'Office'),
        ('Adobe Creative Cloud', 'Adobe Creative Cloud'),
        ('Antivirus', 'Antivirus'),
        ('Otro', 'Otro'),
    ]
    TIPO_ACTIVACION_CHOICES = [
        ('Original / Retail', 'Original / Retail'),
        ('OEM', 'OEM'),
        ('Volumen (KMS/MAK)', 'Volumen (KMS/MAK)'),
        ('Suscripción Digital', 'Suscripción Digital'),
        ('Pendiente de Activación', 'Pendiente de Activación'),
    ]
    ESTADO_LICENCIA_CHOICES = [
        ('Activa', 'Activa'),
        ('Inactiva', 'Inactiva'),
        ('Vencida', 'Vencida'),
    ]

    equipo_asociado = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='licencias')
    tipo_licencia = models.CharField(max_length=50, choices=TIPO_LICENCIA_CHOICES)
    tipo_licencia_otro = models.CharField(max_length=100, blank=True, null=True, verbose_name="¿Cuál otra licencia?")
    tipo_activacion = models.CharField(max_length=50, choices=TIPO_ACTIVACION_CHOICES)
    clave = models.CharField(max_length=255, blank=True, null=True)
    fecha_instalacion = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=50, choices=ESTADO_LICENCIA_CHOICES, default='Activa')
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Licencia de {self.tipo_licencia} para {self.equipo_asociado.nombre}"


class Pasisalvo(models.Model):
    colaborador = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='pasisalvos_generados')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50)
    detalles_pendientes = models.TextField(blank=True, null=True)
    generado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    recibido_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='pasisalvos_recibidos')
    firma_recibido = models.TextField(blank=True, null=True)
    pdf_archivo = models.FileField(upload_to='pasisalvos_pdfs/', blank=True, null=True)

    class Meta:
        verbose_name = "Paz y Salvo"
        verbose_name_plural = "Paz y Salvos"


class HistorialPeriferico(models.Model):
    periferico = models.ForeignKey(Periferico, on_delete=models.SET_NULL, null=True, blank=True)
    periferico_nombre = models.CharField(max_length=200, null=True, blank=True)
    periferico_tipo = models.CharField(max_length=50, null=True, blank=True)
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    equipo_asociado = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    es_baja = models.BooleanField(default=False)

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

    def __str__(self):
        return f"Incidente {self.tipo_incidente} - {self.equipo.nombre}"
