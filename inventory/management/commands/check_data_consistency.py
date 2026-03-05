from django.core.management.base import BaseCommand
from django.db.models import Max
from inventory.models import Equipo
from mantenimientos.models import Mantenimiento

class Command(BaseCommand):
    help = 'Verifies the consistency of data, focusing on maintenance dates and equipment assignments.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data consistency check...'))

        self.check_maintenance_dates()
        self.check_assignment_consistency()

        self.stdout.write(self.style.SUCCESS('Data consistency check complete.'))

    def check_maintenance_dates(self):
        """
        Checks if the denormalized maintenance dates on the Equipo model match the actual
        latest maintenance records. This is a common source of inconsistency.
        """
        self.stdout.write(self.style.HTTP_INFO('\n--- Checking Maintenance Date Consistency ---'))
        inconsistent_equipos = []

        # Using iterator to handle potentially large number of equipos efficiently
        for equipo in Equipo.objects.all().iterator():
            # Find the latest 'Finalizado' maintenance for this equipo
            latest_maintenance = Mantenimiento.objects.filter(
                equipo=equipo,
                estado_mantenimiento='Finalizado'
            ).order_by('-fecha_finalizacion').first()

            actual_last_maintenance_date = latest_maintenance.fecha_finalizacion if latest_maintenance else None
            
            # The field on the model is a DateField, so we need to compare dates.
            equipo_last_maintenance_date = equipo.fecha_ultimo_mantenimiento

            if equipo_last_maintenance_date != actual_last_maintenance_date:
                inconsistent_equipos.append({
                    'equipo_id': equipo.id,
                    'equipo_nombre': equipo.nombre,
                    'equipo_serial': equipo.serial,
                    'expected_date': actual_last_maintenance_date,
                    'actual_date_in_equipo_model': equipo_last_maintenance_date
                })
        
        if not inconsistent_equipos:
            self.stdout.write(self.style.SUCCESS('✅ All equipment maintenance dates are consistent.'))
        else:
            self.stdout.write(self.style.WARNING(f'Found {len(inconsistent_equipos)} equipment records with inconsistent maintenance dates:'))
            for item in inconsistent_equipos:
                self.stdout.write(
                    f"  - Equipo ID {item['equipo_id']} ('{item['equipo_nombre']}'): "
                    f"Expected last maintenance date '{item['expected_date']}' "
                    f"but found '{item['actual_date_in_equipo_model']}'."
                )
            self.stdout.write(self.style.NOTICE(
                'This is likely caused by the outdated maintenance logic in the `inventory` app. '
                'The dates on the Equipo model should be removed to avoid this problem.'
            ))

    def check_assignment_consistency(self):
        """
        Checks if the assignment status of equipment is consistent with whether an
        employee is assigned.
        """
        self.stdout.write(self.style.HTTP_INFO('\n--- Checking Equipment Assignment Consistency ---'))
        inconsistent_assignments = []

        # Check 1: Equipos "Asignado" but no employee linked
        asignado_sin_empleado = Equipo.objects.filter(
            estado_disponibilidad='Asignado',
            empleado_asignado__isnull=True
        )
        for equipo in asignado_sin_empleado:
            inconsistent_assignments.append({
                'equipo_id': equipo.id,
                'equipo_nombre': equipo.nombre,
                'equipo_serial': equipo.serial,
                'issue': "Status is 'Asignado' but has no assigned employee."
            })
            
        # Check 2: Equipos "Disponible" but an employee is linked
        disponible_con_empleado = Equipo.objects.filter(
            estado_disponibilidad='Disponible',
            empleado_asignado__isnull=False
        )
        for equipo in disponible_con_empleado:
            inconsistent_assignments.append({
                'equipo_id': equipo.id,
                'equipo_nombre': equipo.nombre,
                'equipo_serial': equipo.serial,
                'issue': f"Status is 'Disponible' but is assigned to employee ID {equipo.empleado_asignado_id}."
            })

        if not inconsistent_assignments:
            self.stdout.write(self.style.SUCCESS('✅ All equipment assignments are consistent.'))
        else:
            self.stdout.write(self.style.WARNING(f'Found {len(inconsistent_assignments)} equipment records with inconsistent assignments:'))
            for item in inconsistent_assignments:
                self.stdout.write(
                    f"  - Equipo ID {item['equipo_id']} ('{item['equipo_nombre']}'): {item['issue']}"
                )