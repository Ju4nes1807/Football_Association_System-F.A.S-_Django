import time

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ejecuta eliminaciones programadas en un intervalo fijo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Segundos entre revisiones.",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        if interval < 10:
            interval = 10

        self.stdout.write(
            self.style.SUCCESS(
                f"Iniciando eliminaciones programadas cada {interval} segundos."
            )
        )

        try:
            while True:
                call_command("procesar_eliminaciones_programadas", verbosity=0)
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Proceso detenido."))
