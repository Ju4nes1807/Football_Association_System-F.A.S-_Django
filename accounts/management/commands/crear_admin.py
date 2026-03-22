from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from accounts.models import Usuario
from datetime import datetime

class Command(BaseCommand):
    help = 'Crea el primer administrador del sistema'

    def add_arguments(self, parser):
        parser.add_argument('--nombres',    required=True)
        parser.add_argument('--apellidos',  required=True)
        parser.add_argument('--documento',  required=True)
        parser.add_argument('--nacimiento', required=True, help='YYYY-MM-DD')
        parser.add_argument('--email',      required=True)
        parser.add_argument('--telefono',   required=True)
        parser.add_argument('--password',   required=True)
        # Pendiente para cambio
        parser.add_argument('--base-url', default='http://localhost:8000')

    def handle(self, *args, **options):
        if Usuario.objects.filter(_rol=Usuario.Roles.ADMIN).exists():
            raise CommandError('Ya existe un administrador.')

        try:
            user = Usuario()
            user._nombres          = options['nombres']
            user._apellidos        = options['apellidos']
            user._num_documento    = options['documento']
            user._fecha_nacimiento = datetime.strptime(options['nacimiento'], '%Y-%m-%d').date()  # ← fix
            user._email            = options['email']
            user._telefono         = options['telefono']
            user._rol              = Usuario.Roles.ADMIN
            user.set_password(options['password'])
            user.save()
            
            try:
                from accounts.services.email_service import enviar_credenciales_admin
                login_url = options['base_url'].rstrip('/') + reverse('login')
                enviar_credenciales_admin(
                    nombre    = f"{options['nombres']} {options['apellidos']}",
                    email     = options['email'],
                    password  = options['password'],
                    login_url = login_url,
                )
                self.stdout.write(self.style.SUCCESS('📧 Correo enviado.'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️  Admin creado pero el correo falló: {e}'))

            self.stdout.write(self.style.SUCCESS(f'✅ Admin creado: {user._email}'))
        except Exception as e:
            raise CommandError(f'Error: {e}')