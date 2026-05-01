from django.core.management.base import BaseCommand
from django.utils import timezone

from inscripciones.models import Equipo


class Command(BaseCommand):
    help = 'Elimina equipos con eliminacion programada vencida.'

    def handle(self, *args, **options):
        ahora = timezone.now()
        qs = Equipo.objects.filter(
            _eliminar_programada_para__isnull=False,
            _eliminar_programada_para__lte=ahora,
        )
        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No hay equipos para eliminar.'))
            return

        qs.delete()
        self.stdout.write(self.style.SUCCESS(f'Equipos eliminados: {total}'))
