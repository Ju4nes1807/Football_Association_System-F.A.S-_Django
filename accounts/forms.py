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
    fecha_nacimiento = forms.DateField(widget = forms.DateInput(attrs = {'type': 'data'}))
    experiencia = forms.CharField(max_length = 15, required = False)
    password_actual = forms.CharField(required = False, widget = forms.PasswordInput)
    password_nueva = forms.CharField(required = False, widget = forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.initial_pk = kwargs.pop('initial_pk', None)
        super().__init__(*args, **kwargs)

    def clean_num_documento(self):
        num = self.cleaned_data.get('num_documento')
        if Usuario.objects.filter(_num_documento=num).exclude(pk=self.initial_pk).exists():
            raise forms.ValidationError('Este documento ya está registrado.')
        return num

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(_email=email).exclude(pk=self.initial_pk).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono')
        if Usuario.objects.filter(_telefono=tel).exclude(pk=self.initial_pk).exists():
            raise forms.ValidationError('Este teléfono ya está registrado.')
        return tel

    def clean(self):
        cleaned_data = super().clean()
        password_actual = cleaned_data.get('password_actual')
        password_nueva = cleaned_data.get('password_nueva')
        if password_nueva and not password_actual:
            self.add_error('password_actual', 'Debes ingresar tu contraseña actual para cambiarla.')
        return cleaned_data