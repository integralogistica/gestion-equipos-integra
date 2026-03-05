from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User

# Import all models that need to be cleared
from inventory.models import Equipo, Periferico, Licencia, Pasisalvo, HistorialPeriferico, HistorialEquipo
from mantenimientos.models import Mantenimiento
from empleados.models import Empleado
from sede.models import Sede
from usuarios.models import UserProfile

class Command(BaseCommand):
    help = 'Deletes all business data (Equipos, Mantenimientos, etc.) but keeps superusers.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting data deletion process inside a transaction...'))
        self.stdout.write(self.style.WARNING('This will delete all data except for superusers.'))

        # The order of deletion is important to avoid foreign key constraint errors.
        # We delete models that have foreign keys to other models first.
        models_to_delete = [
            HistorialEquipo,
            HistorialPeriferico,
            Mantenimiento,
            Licencia,
            Pasisalvo,
            Periferico,
            Equipo,
            Empleado,
            Sede,
        ]

        for model in models_to_delete:
            model_name = model._meta.verbose_name_plural.capitalize()
            self.stdout.write(f'Deleting all records from {model_name}...'))
            try:
                count, _ = model.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'--> Deleted {count} records from {model_name}.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'An error occurred while deleting {model_name}: {e}'))
                # The transaction will be rolled back.
                raise e

        # Delete UserProfiles of non-superusers
        self.stdout.write('Deleting UserProfile records for non-superusers...')
        try:
            non_superusers = User.objects.filter(is_superuser=False)
            count, _ = UserProfile.objects.filter(user__in=non_superusers).delete()
            self.stdout.write(self.style.SUCCESS(f'--> Deleted {count} UserProfile records.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred while deleting UserProfiles: {e}'))
            raise e

        # Delete non-superuser Users
        self.stdout.write('Deleting non-superuser User records...')
        try:
            # The non_superusers queryset is already defined above
            count, _ = non_superusers.delete()
            self.stdout.write(self.style.SUCCESS(f'--> Deleted {count} non-superuser User records.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred while deleting non-superuser Users: {e}'))
            raise e

        self.stdout.write(self.style.SUCCESS('\nData deletion complete. Superusers have been preserved.'))
