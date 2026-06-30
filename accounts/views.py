from django.contrib import messages

from django.shortcuts import render, redirect
from django.db import IntegrityError
from django.db.models import Q
from django.contrib.auth.views import LoginView
from django.utils import timezone

from inscripciones.views import _get_equipo_entrenador
from .models import Jugador, Usuario, Entrenador
from .forms import RegistroAdminForm, RegistroPublicoForm, EditarPerfilForm
from .services.email_service import enviar_credenciales_admin
from django.urls import reverse, reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from inscripciones.models import Equipo, Cancha
from entrenamientos.models import Entrenamiento
from torneos.models import InscripcionTorneo, Partido, Torneo

def _dashboard_por_rol(user):
    if user.rol == 'ADMIN':
        return 'dashboard_admin'
    if user.rol == 'JUGADOR':
        return 'dashboard_jugador'
    return 'dashboard_entrenador'


def _handle_integrity_error(form, e):
    """Mapea errores de BD al campo correspondiente."""
    err = str(e).lower()
    if 'email'     in err: form.add_error('email',         'Este correo ya está registrado.')
    elif 'document'in err: form.add_error('num_documento', 'Este documento ya está registrado.')
    elif 'telefono'in err: form.add_error('telefono',      'Este teléfono ya está registrado.')
    else:                  form.add_error(None,            'Error al registrar. Verifica tus datos.')

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        form.fields['username'].label = 'Correo Electronico'
        form.fields['username'].widget.attrs['placeholder'] = 'ejemplo@correo.com' 
        return form
    
    def get_success_url(self):
        user = self.request.user
        
        if user.rol == user.Roles.ADMIN:
            return reverse_lazy('dashboard_admin')
        elif user.rol == user.Roles.ENTRENADOR:
            return reverse_lazy('dashboard_entrenador')
        elif user.rol == user.Roles.JUGADOR:
            return reverse_lazy('dashboard_jugador')
        return reverse_lazy('login')
def register(request):
    form = RegistroPublicoForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            user = Entrenador()
            user.nombres          = data['nombres']
            user.apellidos        = data['apellidos']
            user.num_documento    = data['num_documento']
            user.fecha_nacimiento = data['fecha_nacimiento']
            user.email            = data['email']
            user.telefono         = data['telefono']
            user.rol              = Usuario.Roles.ENTRENADOR
            user.experiencia      = data['experiencia']
            user.set_password(data['password'])
            user.save()
            return redirect('login')

        except IntegrityError as e:
            _handle_integrity_error(form, e)
        except ValueError as e:
            form.add_error(None, str(e))

    return render(request, 'accounts/register.html', {'form': form})

@login_required
def register_admin(request):
    # Doble bloqueo: decorador + verificación de rol
    if request.user.rol != Usuario.Roles.ADMIN:
        return redirect('login')

    form = RegistroAdminForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            user = Usuario()
            user.nombres          = data['nombres']
            user.apellidos        = data['apellidos']
            user.num_documento    = data['num_documento']
            user.fecha_nacimiento = data['fecha_nacimiento']
            user.email            = data['email']
            user.telefono         = data['telefono']
            user.rol              = Usuario.Roles.ADMIN
            user.set_password(data['password'])
            user.save()
            try:
                enviar_credenciales_admin(
                    nombre    = f"{data['nombres']} {data['apellidos']}",
                    email     = data['email'],
                    password  = data['password'],
                    login_url = request.build_absolute_uri(reverse('login')),
                )
            except Exception:
                pass  # el usuario se creó aunque el correo falle
            return redirect('dashboard_admin')

        except IntegrityError as e:
            _handle_integrity_error(form, e)
        except ValueError as e:
            form.add_error(None, str(e))

    return render(request, 'accounts/register_admin.html', {'form': form})

@login_required
def editar_perfil(request):
    user = request.user
    es_entrenador = user.rol == user.Roles.ENTRENADOR

    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, initial_pk = user.pk, es_entrenador = es_entrenador)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user.nombres          = data['nombres']
                user.apellidos        = data['apellidos']
                user.num_documento    = data['num_documento']
                user.email            = data['email']
                user.telefono         = data['telefono']
                user.fecha_nacimiento = data['fecha_nacimiento']

                # Solo entrenador
                if user.rol == user.Roles.ENTRENADOR:
                    user.entrenador.experiencia = data['experiencia']
                    user.entrenador.save()

                # Cambio de contraseña
                password_actual = data.get('password_actual')
                password_nueva  = data.get('password_nueva')
                if password_actual and password_nueva:
                    if user.check_password(password_actual):
                        user.set_password(password_nueva)
                        update_session_auth_hash(request, user)
                        messages.success(request, 'Contraseña actualizada correctamente.')
                    else:
                        form.add_error('password_actual', 'La contraseña actual es incorrecta.')
                        return render(request, 'accounts/roles/editar_perfil.html', {'form': form})

                user.save()
                messages.success(request, 'Perfil actualizado correctamente.')
                return redirect('editar_perfil')

            except ValueError as e:
                form.add_error(None, str(e))
            except IntegrityError as e:
                err = str(e).lower()
                if 'num_documento' in err:
                    form.add_error('num_documento', 'Este documento ya está registrado.')
                elif 'email' in err:
                    form.add_error('email', 'Este correo ya está registrado.')
                elif 'telefono' in err:
                    form.add_error('telefono', 'Este teléfono ya está registrado.')
                else:
                    form.add_error(None, 'Error al actualizar. Verifica tus datos.')

    else:
        # Prellenar el form con los datos actuales
        initial = {
            'nombres':          user.nombres,
            'apellidos':        user.apellidos,
            'num_documento':    user.num_documento,
            'email':            user.email,
            'telefono':         user.telefono,
            'fecha_nacimiento': user.fecha_nacimiento,
        }
        if es_entrenador:
            initial['experiencia'] = user.entrenador.experiencia

        form = EditarPerfilForm(initial=initial, initial_pk = user.pk, es_entrenador = es_entrenador)

    return render(request, 'accounts/roles/editar_perfil.html', {'form': form})
@login_required
def dashboard_admin(request):
    if request.user.rol != 'ADMIN':
        return redirect(_dashboard_por_rol(request.user))

    equipos_pendientes = Equipo.objects.filter(_estado=Equipo.Estado.ESPERA).count()
    torneos_activos = Torneo.objects.filter(estado__in=[Torneo.Estado.PROXIMO, Torneo.Estado.EN_CURSO]).count()
    partidos_pendientes = Partido.objects.exclude(estado__in=['FINALIZADO', 'SUSPENDIDO']).count()
    equipos_eliminacion = Equipo.objects.filter(_eliminar_programada_para__isnull=False).count()
    notificaciones = []
    if equipos_pendientes:
        notificaciones.append(f'Hay {equipos_pendientes} equipo(s) esperando revision.')
    if equipos_eliminacion:
        notificaciones.append(f'{equipos_eliminacion} equipo(s) tienen eliminacion programada.')
    if partidos_pendientes:
        notificaciones.append(f'{partidos_pendientes} partido(s) siguen pendientes de gestion.')
    if not notificaciones:
        notificaciones.append('El panel administrativo esta al dia. Buen momento para revisar calendario y canchas.')

    return render(request, 'accounts/roles/dashboardAdmin.html', {
        'total_equipos': Equipo.objects.count(),
        'total_canchas': Cancha.objects.count(),
        'total_entrenadores': Entrenador.objects.count(),
        'total_jugadores': Jugador.objects.count(),
        'equipos_pendientes': equipos_pendientes,
        'torneos_activos': torneos_activos,
        'partidos_pendientes': partidos_pendientes,
        'equipos_eliminacion': equipos_eliminacion,
        'ultimos_equipos': Equipo.objects.select_related('entrenador').order_by('-fecha_registro')[:4],
        'notificaciones': notificaciones,
    })


@login_required
def dashboard_entrenador(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect(_dashboard_por_rol(request.user))

    equipo          = _get_equipo_entrenador(request) if hasattr(request.user, 'entrenador') else None
    equipos         = request.user.entrenador.equipos.order_by('_nombre')
    total_jugadores = Jugador.objects.filter(equipo=equipo).count() if equipo else 0
    total_canchas   = Cancha.objects.filter(_disponibilidad='DISPONIBLE').count()
    total_entrenamientos = Entrenamiento.objects.filter(equipo=equipo).count() if equipo else 0
    ahora = timezone.now()
    proximos_entrenamientos = Entrenamiento.objects.filter(equipo=equipo, fecha_hora__gte=ahora).order_by('fecha_hora')[:3] if equipo else []
    torneos_activos = InscripcionTorneo.objects.filter(
        equipo=equipo,
        estado='ACTIVA',
        torneo__estado__in=[Torneo.Estado.PROXIMO, Torneo.Estado.EN_CURSO],
    ).select_related('torneo').count() if equipo else 0
    partidos_pendientes = 0
    if equipo:
        partidos_pendientes = Partido.objects.filter(
            Q(equipo_local=equipo) | Q(equipo_visita=equipo)
        ).exclude(estado__in=['FINALIZADO', 'SUSPENDIDO']).count()

    notificaciones = []
    if not equipo:
        notificaciones.append('Registra o asocia tu equipo para activar entrenamientos, torneos y reportes.')
    elif total_jugadores == 0:
        notificaciones.append('Tu equipo aun no tiene jugadores. Agrega la plantilla para usar asistencia y reportes.')
    elif partidos_pendientes:
        notificaciones.append(f'Tienes {partidos_pendientes} partido(s) pendiente(s) por revisar.')
    else:
        notificaciones.append('Tu tablero esta al dia. Buen momento para planear la proxima sesion.')

    return render(request, 'accounts/roles/dashboardEntrenador.html', {
        'equipo':          equipo,
        'equipos':         equipos,
        'total_jugadores': total_jugadores,
        'total_canchas':   total_canchas,
        'total_entrenamientos': total_entrenamientos,
        'proximos_entrenamientos': proximos_entrenamientos,
        'torneos_activos': torneos_activos,
        'partidos_pendientes': partidos_pendientes,
        'notificaciones': notificaciones,
    })

@login_required
def dashboard_jugador(request):
    if request.user.rol != 'JUGADOR':
        return redirect(_dashboard_por_rol(request.user))

    user    = request.user
    jugador = getattr(user, 'jugador', None)
    equipo  = jugador.equipo if jugador else None
    ahora = timezone.now()
    proximos_entrenamientos = Entrenamiento.objects.filter(equipo=equipo, fecha_hora__gte=ahora).order_by('fecha_hora')[:3] if equipo else []
    proximos_partidos = Partido.objects.filter(
        Q(equipo_local=equipo) | Q(equipo_visita=equipo),
        fecha__gte=ahora,
    ).exclude(estado__in=['FINALIZADO', 'SUSPENDIDO']).select_related('torneo', 'equipo_local', 'equipo_visita').order_by('fecha')[:3] if equipo else []
    torneos_activos = InscripcionTorneo.objects.filter(
        equipo=equipo,
        estado='ACTIVA',
        torneo__estado__in=[Torneo.Estado.PROXIMO, Torneo.Estado.EN_CURSO],
    ).count() if equipo else 0
    notificaciones = []
    if not equipo:
        notificaciones.append('Aun no tienes equipo asignado. Cuando te vinculen, aqui veras tu agenda.')
    elif proximos_partidos:
        notificaciones.append(f'Tienes {len(proximos_partidos)} partido(s) proximos en agenda.')
    elif proximos_entrenamientos:
        notificaciones.append(f'Tienes {len(proximos_entrenamientos)} entrenamiento(s) proximos.')
    else:
        notificaciones.append('No tienes eventos proximos registrados. Mantente atento a nuevas programaciones.')

    return render(request, 'accounts/roles/dashboardJugador.html', {
        'jugador': jugador,
        'equipo':  equipo,
        'proximos_entrenamientos': proximos_entrenamientos,
        'proximos_partidos': proximos_partidos,
        'torneos_activos': torneos_activos,
        'notificaciones': notificaciones,
    })

@login_required
def mi_equipo_jugador(request):
    if request.user.rol != 'JUGADOR':
        return redirect(_dashboard_por_rol(request.user))

    jugador = getattr(request.user, 'jugador', None)
    equipo  = jugador.equipo if jugador else None

    return render(request, 'accounts/roles/mi_equipo_jugador.html', {
        'equipo': equipo,
    })
