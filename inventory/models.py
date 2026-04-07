from django.db import models
from django.conf import settings
from empleados.models import Empleado
from sede.models import Sede
from django.contrib.auth.models import AbstractUser





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
    estado_tecnico = models.CharField(max_length=50, choices=[('Nuevo', 'Nuevo'), ('Reacondicionado', 'Reacondicionado')], default='Nuevo', verbose_name="Estado Técnico")
    estado_disponibilidad = models.CharField(max_length=50, choices=[('Disponible', 'Disponible'), ('Asignado', 'Asignado'), ('Reservado', 'Reservado'), ('No disponible por daño', 'No disponible por mantenimiento')], default='Disponible', verbose_name="Estado de Disponibilidad")
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sede")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    # --- SECCIÓN: A Cargo de ---
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos_asignados', verbose_name="Empleado Asignado")
    fecha_entrega_a_colaborador = models.DateField(null=True, blank=True, verbose_name="Fecha de Entrega a Colaborador")
    
    # --- SECCIÓN: Custodia Temporal (cuando está disponible pero bajo cargo de alguien) ---
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
    estado_fisico = models.TextField(blank=True, null=True, verbose_name="Estado Físico Actual (Detalles estéticos/golpes)")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas Internas (TI)")
    
    # --- Imagen del Equipo ---
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
        ('Devuelto', 'Devuelto'), # Aunque "Devuelto" es más un evento, lo incluimos como estado si es necesario.
    ]

    nombre = models.CharField(max_length=100, help_text="Nombre o descripción del periférico, ej: Mouse Logitech G203")
    tipo = models.CharField(max_length=50, choices=TIPO_PERIFERICO_CHOICES)
    estado_tecnico = models.CharField(max_length=50, choices=ESTADO_TECNICO_CHOICES, default='Funcional')
    estado_disponibilidad = models.CharField(max_length=50, choices=ESTADO_DISPONIBILIDAD_CHOICES, default='Disponible')
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='perifericos_asignados')
    equipo_asociado = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='perifericos')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name='perifericos', verbose_name="Sede")
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

class Licencia(models.Model):
    TIPO_LICENCIA_CHOICES = [
        ('Sistema Operativo', 'Sistema Operativo'),
        ('Office', 'Office'),
        ('Otro', 'Otro'),
    ]
    TIPO_ACTIVACION_CHOICES = [
        ('Original', 'Original'),
        ('Pirateada', 'Pirateada'),
        ('OEM', 'OEM'),
        ('Volumen', 'Volumen'),
    ]
    ESTADO_LICENCIA_CHOICES = [
        ('Activa', 'Activa'),
        ('Inactiva', 'Inactiva'),
        ('Vencida', 'Vencida'),
    ]

    equipo_asociado = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='licencias')
    tipo_licencia = models.CharField(max_length=50, choices=TIPO_LICENCIA_CHOICES)
    tipo_activacion = models.CharField(max_length=50, choices=TIPO_ACTIVACION_CHOICES)
    clave = models.CharField(max_length=255, blank=True, null=True)
    fecha_instalacion = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=50, choices=ESTADO_LICENCIA_CHOICES, default='Activa')
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Licencia de {self.tipo_licencia} para {self.equipo_asociado.nombre}"

class Pasisalvo(models.Model):
    ESTADO_PASISALVO_CHOICES = [
        ('Aprobado', 'Aprobado'),
        ('Con Pendientes', 'Con Pendientes'),
        ('Rechazado', 'Rechazado'), # Si no se puede aprobar debido a problemas graves
    ]

    colaborador = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='pasisalvos_generados')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name='pasisalvos', verbose_name="Sede")
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50, choices=ESTADO_PASISALVO_CHOICES)
    detalles_pendientes = models.TextField(blank=True, null=True, help_text="Detalles de equipos, periféricos o mantenimientos pendientes.")
    generado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pasisalvos_creados_por_admin')
    
    # Nuevos campos para el receptor de los equipos
    recibido_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='pasisalvos_recibidos', verbose_name="Recibido por (Custodio)")
    firma_recibido = models.TextField(blank=True, null=True, verbose_name="Firma de quien recibe")
    
    pdf_archivo = models.FileField(upload_to='pasisalvos_pdfs/', blank=True, null=True, help_text='Archivo PDF del pasisalvo generado.')

    class Meta:
        verbose_name = "Paz y Salvo"
        verbose_name_plural = "Paz y Salvos"
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"Paz y Salvo para {self.colaborador} - {self.estado}"
    
class HistorialPeriferico(models.Model):
    """
    Modelo para registrar el historial de asignación de periféricos.
    """
    periferico = models.ForeignKey(Periferico, on_delete=models.SET_NULL, null=True, blank=True, related_name='historial')
    periferico_nombre = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nombre del Periférico (Histórico)")
    periferico_tipo = models.CharField(max_length=50, null=True, blank=True, verbose_name="Tipo de Periférico (Histórico)")
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Empleado Asignado")
    equipo_asociado = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Equipo Asociado en la Entrega")
    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Asignación")
    fecha_devolucion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Devolución")
    observacion_devolucion = models.TextField(blank=True, null=True, verbose_name="Observación de Devolución")
    es_baja = models.BooleanField(default=False, verbose_name="Fue dado de baja")
    fecha_baja = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Baja")

    def save(self, *args, **kwargs):
        if self.periferico:
            if not self.periferico_nombre:
                self.periferico_nombre = self.periferico.nombre
            if not self.periferico_tipo:
                self.periferico_tipo = self.periferico.tipo
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Historial de Periférico"
        verbose_name_plural = "Historial de Periféricos"
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"Historial de {self.periferico.nombre}"

class HistorialEquipo(models.Model):
    """
    Registra el historial de cambios de un equipo.
    """
    TIPO_ACCION_CHOICES = [
        ('CREADO', 'Creado'),
        ('ACTUALIZADO', 'Actualizado'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='historial_cambios')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuario que realizó el cambio")
    fecha_cambio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Cambio")
    campo_modificado = models.CharField(max_length=100, verbose_name="Campo Modificado")
    valor_anterior = models.TextField(null=True, blank=True, verbose_name="Valor Anterior")
    valor_nuevo = models.TextField(null=True, blank=True, verbose_name="Valor Nuevo")
    tipo_accion = models.CharField(max_length=20, choices=TIPO_ACCION_CHOICES, verbose_name="Tipo de Acción")

    class Meta:
        verbose_name = "Historial de Equipo"
        verbose_name_plural = "Historial de Equipos"
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"Cambio en {self.equipo.nombre} por {self.usuario.username if self.usuario else 'Sistema'} el {self.fecha_cambio.strftime('%Y-%m-%d %H:%M')}"

class HistorialMovimientoEquipo(models.Model):
    """
    Modelo para registrar el historial de asignación de equipos.
    Captura el estado completo del equipo al momento de la entrega y al momento de la devolución.
    """
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='historial_movimientos')
    equipo_nombre = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nombre del Equipo (Histórico)")
    equipo_serial = models.CharField(max_length=100, null=True, blank=True, verbose_name="Serial del Equipo (Histórico)")
    
    # --- FOTO AL MOMENTO DE LA ENTREGA ---
    ram_entrega = models.CharField(max_length=20, blank=True, null=True, verbose_name="RAM (Entrega)")
    rom_entrega = models.CharField(max_length=20, blank=True, null=True, verbose_name="Disco (Entrega)")
    so_entrega = models.CharField(max_length=100, blank=True, null=True, verbose_name="S.O. (Entrega)")
    procesador_entrega = models.CharField(max_length=100, blank=True, null=True, verbose_name="Procesador (Entrega)")
    estado_tecnico_entrega = models.CharField(max_length=50, blank=True, null=True, verbose_name="Estado Técnico (Entrega)")
    antivirus_entrega = models.CharField(max_length=100, blank=True, null=True, verbose_name="Antivirus (Entrega)")
    usuarios_sistema_entrega = models.TextField(blank=True, null=True, verbose_name="Usuarios Sistema (Entrega)")
    redes_conectadas_entrega = models.TextField(blank=True, null=True, verbose_name="Redes (Entrega)")
    estado_fisico_entrega = models.TextField(blank=True, null=True, verbose_name="Estado Físico (Entrega/Salida)")

    # --- FOTO AL MOMENTO DE LA DEVOLUCIÓN ---
    ram_devolucion = models.CharField(max_length=20, blank=True, null=True, verbose_name="RAM (Devolución)")
    rom_devolucion = models.CharField(max_length=20, blank=True, null=True, verbose_name="Disco (Devolución)")
    so_devolucion = models.CharField(max_length=100, blank=True, null=True, verbose_name="S.O. (Devolución)")
    procesador_devolucion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Procesador (Devolución)")
    estado_fisico_devolucion = models.TextField(blank=True, null=True, verbose_name="Estado Físico (Entrada/Recibo)")

    # --- METADATOS DEL MOVIMIENTO ---
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Empleado Asignado")
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name='historial_movimientos_equipos', verbose_name="Sede")
    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Asignación")
    fecha_devolucion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Devolución")
    observacion_devolucion = models.TextField(blank=True, null=True, verbose_name="Observaciones Generales")
    es_baja = models.BooleanField(default=False, verbose_name="Fue dado de baja")
    fecha_baja = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Baja")

    def save(self, *args, **kwargs):
        if self.equipo and not self.pk: # Solo al crear el registro inicial (Entrega)
            if not self.equipo_nombre:
                self.equipo_nombre = self.equipo.nombre
            if not self.equipo_serial:
                self.equipo_serial = self.equipo.serial
            
            # Capturar specs de entrega
            self.ram_entrega = self.equipo.ram
            self.rom_entrega = self.equipo.rom
            self.so_entrega = self.equipo.sistema_operativo
            self.procesador_entrega = self.equipo.procesador
            self.estado_tecnico_entrega = self.equipo.estado_tecnico
            self.antivirus_entrega = self.equipo.antivirus
            self.usuarios_sistema_entrega = self.equipo.usuarios_sistema
            self.redes_conectadas_entrega = self.equipo.redes_conectadas
            self.estado_fisico_entrega = self.equipo.estado_fisico
            
            if not self.sede and self.equipo.sede:
                self.sede = self.equipo.sede
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Historial de Movimiento de Equipo"
        verbose_name_plural = "Historial de Movimientos de Equipos"
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"Movimiento de {self.equipo_nombre} - {self.equipo_serial}"

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
    fecha_incidente = models.DateField(auto_now_add=True)
    resolucion = models.CharField(max_length=50, choices=RESOLUCION_CHOICES, default='Reparación Interna')
    equipo_nuevo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='reposicion_de')
    evidencia_foto = models.ImageField(upload_to='incidentes_fotos/', null=True, blank=True)
    costo_estimado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    creado_en = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Incidente {self.tipo_incidente} - {self.equipo.nombre}"
