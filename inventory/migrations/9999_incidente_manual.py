from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0020_equipo_antivirus_equipo_redes_conectadas_and_more'), # Asumo que la 0020 es la última
    ]

    operations = [
        migrations.CreateModel(
            name='ReporteIncidente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_incidente', models.CharField(choices=[('Caída / Golpe', 'Caída / Golpe'), ('Derrame de Líquido', 'Derrame de Líquido'), ('Robo / Pérdida', 'Robo / Pérdida'), ('Falla Técnica Grave', 'Falla Técnica Grave'), ('Desgaste Natural', 'Desgaste Natural'), ('Uso Indebido', 'Uso Indebido'), ('Otro', 'Otro')], max_length=50)),
                ('descripcion', models.TextField()),
                ('fecha_incidente', models.DateField(auto_now_add=True)),
                ('resolucion', models.CharField(choices=[('Reparación Interna', 'Reparación Interna'), ('Garantía Fabricante', 'Garantía Fabricante'), ('Baja Total - Reposición', 'Baja Total - Reposición'), ('Cargo a Colaborador', 'Cargo a Colaborador'), ('Cerrado sin Acción', 'Cerrado sin Acción')], default='Reparación Interna', max_length=50)),
                ('evidencia_foto', models.ImageField(blank=True, null=True, upload_to='incidentes_fotos/')),
                ('costo_estimado', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('empleado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='empleados.empleado')),
                ('equipo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incidentes', to='inventory.equipo')),
                ('equipo_nuevo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reposicion_de', to='inventory.equipo')),
            ],
        ),
    ]
