from datetime import date
import re

from django import forms
from django.contrib.auth.forms import PasswordResetForm
from .models import Usuario, Entrenador

class BaseRegistroForm(forms.Form):
    nombres          = forms.CharField(max_length=50)
    apellidos        = forms.CharField(max_length=50)
    num_documento    = forms.CharField()
    fecha_nacimiento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    email            = forms.EmailField()
    telefono         = forms.CharField(max_length=20)
    password         = forms.CharField(widget=forms.PasswordInput)

    def clean_num_documento(self):
        num = self.cleaned_data.get('num_documento')
        if Usuario.objects.filter(_num_documento=num).exists():
            raise forms.ValidationError('Este documento ya está registrado.')
        return num

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(_email=email).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono')
        if Usuario.objects.filter(_telefono=tel).exists():
            raise forms.ValidationError('Este teléfono ya está registrado.')
        return tel

class RegistroPublicoForm(BaseRegistroForm):
    experiencia = forms.CharField(max_length=15)

class RegistroAdminForm(BaseRegistroForm):
    pass

class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        return Usuario.objects.filter(
            _email__iexact=email,
            is_active=True
        )

class EditarPerfilForm(forms.Form):
    nombres = forms.CharField(max_length = 50)
    apellidos = forms.CharField(max_length = 50)
    num_documento = forms.CharField()
    email = forms.EmailField()
    telefono = forms.CharField(max_length = 20)
    fecha_nacimiento = forms.DateField(widget = forms.DateInput(attrs = {'type': 'date'}))
    experiencia = forms.CharField(max_length = 15, required = False)
    password_actual = forms.CharField(required = False, widget = forms.PasswordInput)
    password_nueva = forms.CharField(required = False, widget = forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.initial_pk = kwargs.pop('initial_pk', None)
        self.es_entrenador = kwargs.pop('es_entrenador', False)
        super().__init__(*args, **kwargs)
        self.fields['experiencia'].required = self.es_entrenador

    def clean_nombres(self):
        nombres = (self.cleaned_data.get('nombres') or '').strip()
        if not nombres:
            raise forms.ValidationError('El nombre es obligatorio.')
        if len(nombres) < 2:
            raise forms.ValidationError('Mínimo 2 caracteres.')
        if not re.match(r'^[a-záéíóúüñA-ZÁÉÍÓÚÜÑ\s]+$', nombres):
            raise forms.ValidationError('Solo letras y espacios.')
        return nombres

    def clean_apellidos(self):
        apellidos = (self.cleaned_data.get('apellidos') or '').strip()
        if not apellidos:
            raise forms.ValidationError('Los apellidos son obligatorios.')
        if len(apellidos) < 2:
            raise forms.ValidationError('Mínimo 2 caracteres.')
        if not re.match(r'^[a-záéíóúüñA-ZÁÉÍÓÚÜÑ\s]+$', apellidos):
            raise forms.ValidationError('Solo letras y espacios.')
        return apellidos

    def clean_num_documento(self):
        num = (self.cleaned_data.get('num_documento') or '').strip()
        if not num:
            raise forms.ValidationError('El número de documento es obligatorio.')
        if not re.match(r'^\d{6,12}$', num):
            raise forms.ValidationError('Entre 6 y 12 dígitos numéricos.')
        if Usuario.objects.filter(_num_documento=num).exclude(pk=self.initial_pk).exists():
            raise forms.ValidationError('Este documento ya está registrado.')
        return num

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise forms.ValidationError('El correo es obligatorio.')
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', email):
            raise forms.ValidationError('Ingresa un correo válido.')
        if Usuario.objects.filter(_email=email).exclude(pk=self.initial_pk).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email

    def clean_telefono(self):
        tel = (self.cleaned_data.get('telefono') or '').strip()
        if not tel:
            raise forms.ValidationError('El teléfono es obligatorio.')
        if not re.match(r'^3[0-9]{9}$', tel):
            raise forms.ValidationError('Número colombiano válido (ej: 3001234567).')
        if Usuario.objects.filter(_telefono=tel).exclude(pk=self.initial_pk).exists():
            raise forms.ValidationError('Este teléfono ya está registrado.')
        return tel

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if not fecha:
            raise forms.ValidationError('La fecha de nacimiento es obligatoria.')
        hoy = date.today()
        if fecha > hoy:
            raise forms.ValidationError('La fecha no puede ser futura.')
        edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        if edad < 20:
            raise forms.ValidationError('Debes tener al menos 20 años.')
        if edad > 100:
            raise forms.ValidationError('Fecha inválida.')
        return fecha

    def clean_experiencia(self):
        experiencia = (self.cleaned_data.get('experiencia') or '').strip()
        if not self.es_entrenador:
            return experiencia
        if not experiencia:
            raise forms.ValidationError('La experiencia es obligatoria.')
        if len(experiencia) > 15:
            raise forms.ValidationError('Máximo 15 caracteres.')
        return experiencia

    def clean_password_nueva(self):
        password = self.cleaned_data.get('password_nueva')
        if not password:
            return password
        if len(password) < 8:
            raise forms.ValidationError('Mínimo 8 caracteres.')
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError('Debe incluir una mayúscula.')
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError('Debe incluir un número.')
        if not re.search(r'[^a-zA-Z0-9]', password):
            raise forms.ValidationError('Debe incluir un carácter especial.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password_actual = cleaned_data.get('password_actual')
        password_nueva = cleaned_data.get('password_nueva')
        if password_nueva and not password_actual:
            self.add_error('password_actual', 'Debes ingresar tu contraseña actual para cambiarla.')
        return cleaned_data