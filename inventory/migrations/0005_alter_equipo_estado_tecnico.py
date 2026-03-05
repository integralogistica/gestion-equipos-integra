from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_alter_historialperiferico_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipo',
            name='estado_tecnico',
            field=models.CharField(choices=[('Nuevo', 'Nuevo'), ('Reacondicionado', 'Reacondicionado')], default='Nuevo', max_length=50, verbose_name='Estado Técnico'),
        ),
    ]
