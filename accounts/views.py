from django.contrib import messages

from django.shortcuts import render, redirect
from django.db import IntegrityError
from django.contrib.auth.views import LoginView
from .models import Usuario, Entrenador
from .forms import BaseRegistroForm, RegistroAdminForm, RegistroPublicoForm, EditarPerfilForm
from .services.email_service import enviar_credenciales_admin
from django.urls import reverse, reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from inscripciones.models import Equipo

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
                    password  = data['password'],  # antes del hash
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

    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, initial_pk = user.pk)
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
        if user.rol == user.Roles.ENTRENADOR:
            initial['experiencia'] = user.entrenador.experiencia

        form = EditarPerfilForm(initial=initial, initial_pk = user.pk)

    return render(request, 'accounts/roles/editar_perfil.html', {'form': form})
@login_required
def dashboard_admin(request):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    total_equipos = Equipo.objects.count()

    return render(request, 'accounts/roles/dashboardAdmin.html', {
        'total_equipos': total_equipos,
    })

@login_required
def dashboard_entrenador(request):
    return render(request, 'accounts/roles/dashboardEntrenador.html')

@login_required
def dashboard_jugador(request):
    return render(request, 'accounts/roles/dashboardJugador.html')