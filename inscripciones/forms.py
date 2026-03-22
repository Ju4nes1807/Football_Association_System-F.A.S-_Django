from datetime import date
from .models import Cancha, Equipo
from accounts.models import Jugador, Usuario
from .utils import validar_edad_categoria
from django import forms

POSICIONES = [
    ('', 'Seleccione una posición'),
    ('portero', 'Portero'),
    ('defensa', 'Defensa'),
    ('lateral derecho', 'Lateral Derecho'),
    ('lateral izquierdo', 'Lateral Izquierdo'),
    ('central', 'Central'),
    ('mediocampista', 'Mediocampista'),
    ('volante', 'Volante'),
    ('extremo derecho', 'Extremo Derecho'),
    ('extremo izquierdo', 'Extremo Izquierdo'),
    ('delantero', 'Delantero'),
    ('centrodelantero', 'Centrodelantero'),
]

PIES = [
    ('', 'Seleccione'),
    ('derecho', 'Derecho'),
    ('izquierdo', 'Izquierdo'),
    ('ambos', 'Ambos'),
]

class RegistroEquipoForm(forms.Form):
    nombre = forms.CharField(max_length = 100)
    descripcion = forms.CharField(widget = forms.Textarea, required = False)
    anio_fundacion = forms.IntegerField()
    logo = forms.ImageField(required = False)
    categoria = forms.ChoiceField(
        choices = [('', 'Seleccione una categoria')] + list(Equipo.Categoria.choices)
    )
    localidad = forms.CharField(max_length = 100)
    barrio = forms.CharField(max_length = 100)

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if Equipo.objects.filter(_nombre__iexact=nombre).exists():
            raise forms.ValidationError('Ya existe un equipo con ese nombre.')
        return nombre
    
    def clean_anio_fundacion(self):
        anio = self.cleaned_data.get('anio_fundacion')
        if anio < 1900 or anio > date.today().year:
            raise forms.ValidationError(f'Año inválido. Entre 1900 y {date.today().year}.')
        return anio
    
    def clean_categoria(self):
        cat = self.cleaned_data.get('categoria')
        if not cat:
            raise forms.ValidationError('Debes seleccionar una categoría.')
        return cat

class EditarEquipoForm(forms.Form):
    nombre         = forms.CharField(max_length=100)
    descripcion    = forms.CharField(widget=forms.Textarea, required=False)
    anio_fundacion = forms.IntegerField()
    logo           = forms.ImageField(required=False)
    categoria      = forms.ChoiceField(
        choices=[('', 'Seleccione una categoría')] + list(Equipo.Categoria.choices)
    )
    localidad      = forms.CharField(max_length=100)
    barrio         = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        self.equipo_pk = kwargs.pop('equipo_pk', None)
        super().__init__(*args, **kwargs)

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        qs = Equipo.objects.filter(_nombre__iexact=nombre)
        if self.equipo_pk:
            qs = qs.exclude(pk=self.equipo_pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un equipo con ese nombre.')
        return nombre

    def clean_anio_fundacion(self):
        anio = self.cleaned_data.get('anio_fundacion')
        if anio < 1900 or anio > date.today().year:
            raise forms.ValidationError(f'Año inválido. Entre 1900 y {date.today().year}.')
        return anio

class RegistroJugadorForm(forms.Form):
    nombres = forms.CharField(max_length = 50)
    apellidos = forms.CharField(max_length = 50)
    num_documento = forms.CharField()
    fecha_nacimiento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    email = forms.EmailField()
    telefono = forms.CharField(max_length = 20)
    password = forms.CharField(widget = forms.PasswordInput)
    dorsal = forms.IntegerField(min_value = 1, max_value = 99)
    pie_dominante = forms.ChoiceField(choices = PIES)
    posicion = forms.ChoiceField(choices = POSICIONES)

    def __init__(self, *args, **kwargs):
        self.equipo = kwargs.pop('equipo', None)
        super().__init__(*args, **kwargs)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(_email = email).exists():
            raise forms.ValidationError('Este correo ya esta registrado.')
        return email
    
    def clean_num_documento(self):
        num = self.cleaned_data.get('num_documento')
        if Usuario.objects.filter(_num_documento = num).exists():
            raise forms.ValidationError('Este documento ya esta registrado.')
        return num
    
    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono')
        if Usuario.objects.filter(_telefono=tel).exists():
            raise forms.ValidationError('Este teléfono ya está registrado.')
        return tel

    def clean_dorsal(self):
        dorsal = self.cleaned_data.get('dorsal')
        if self.equipo:
            if Jugador.objects.filter(equipo=self.equipo, _dorsal=dorsal).exists():
                raise forms.ValidationError(f'El dorsal {dorsal} ya está en uso en este equipo.')
        return dorsal

    def clean_password(self):
        password = self.cleaned_data.get('password')
        import re
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
        cleaned_data     = super().clean()
        fecha_nacimiento = cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento and self.equipo:
            valido, msg = validar_edad_categoria(fecha_nacimiento, self.equipo.categoria)
            if not valido:
                self.add_error('fecha_nacimiento', msg)
        return cleaned_data
    
class CargaMasivaJugadoresForm(forms.Form):
    archivo = forms.FileField()

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        nombre  = archivo.name.lower()
        if not (nombre.endswith('.xlsx') or nombre.endswith('.csv')):
            raise forms.ValidationError('Solo se permiten archivos .xlsx o .csv')
        if archivo.size > 5 * 1024 * 1024:
            raise forms.ValidationError('El archivo no puede superar 5MB.')
        return archivo

class EditarJugadorEntrenadorForm(forms.Form):
    dorsal = forms.IntegerField(min_value = 1, max_value = 99)
    pie_dominante = forms.ChoiceField(choices = PIES)
    posicion = forms.ChoiceField(choices = POSICIONES)

    def __init__(self, *args, **kwargs):
        self.jugador_pk = kwargs.pop('jugador_pk', None)
        self.equipo     = kwargs.pop('equipo', None)
        super().__init__(*args, **kwargs)

    def clean_dorsal(self):
        dorsal = self.cleaned_data.get('dorsal')
        if self.equipo:
            if Jugador.objects.filter(
                equipo=self.equipo,
                _dorsal=dorsal
            ).exclude(pk=self.jugador_pk).exists():
                raise forms.ValidationError(f'El dorsal {dorsal} ya está en uso.')
        return dorsal

class EditarPerfilJugadorForm(forms.Form):
    nombres = forms.CharField(max_length = 50)
    apellidos = forms.CharField(max_length = 50)
    num_documento = forms.CharField()
    email = forms.EmailField()
    telefono = forms.CharField(max_length = 20)
    password_actual = forms.CharField(required=False, widget=forms.PasswordInput)
    password_nueva  = forms.CharField(required=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.jugador_pk = kwargs.pop('jugador_pk', None)
        super().__init__(*args, **kwargs)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(_email = email).exclude(pk = self.jugador_pk).exists():
            raise forms.ValidationError('El correo ya esta en uso.')
        return email
    
    def clean_num_documento(self):
        num = self.cleaned_data.get('num_documento')
        if Usuario.objects.filter(_num_documento = num).exclude(pk = self.jugador_pk).exists():
            raise forms.ValidationError('El numero de documento ya esta registrado.')
        return num
    
    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono')
        if Usuario.objects.filter(_telefono = tel).exclude(pk = self.jugador_pk).exists():
            raise forms.ValidationError('El numero de telefono ya esta en uso.')
        return tel
    
    def clean_password_nueva(self):
        password = self.cleaned_data.get('password_nueva')
        if not password:
            return password
        import re
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
        cleaned_data    = super().clean()
        password_actual = cleaned_data.get('password_actual')
        password_nueva  = cleaned_data.get('password_nueva')
        if password_nueva and not password_actual:
            self.add_error('password_actual', 'Debes ingresar tu contraseña actual.')
        return cleaned_data

class CanchaForm(forms.Form):
    codigo_idrd           = forms.CharField(max_length=50, required=False)
    nombre_escenario      = forms.CharField(max_length=150)
    localidad             = forms.CharField(max_length=100)
    barrio                = forms.CharField(max_length=100)
    direccion_exacta      = forms.CharField(max_length=200)
    codigo_rupi           = forms.CharField(max_length=50, required=False)
    tipo_disciplina       = forms.ChoiceField(choices=[('', 'Seleccione')] + list(Cancha.TipoDisciplina.choices))
    tipo_superficie       = forms.ChoiceField(choices=[('', 'Seleccione')] + list(Cancha.TipoSuperficie.choices))
    medidas_area          = forms.CharField(max_length=50)
    estado_conservacion   = forms.ChoiceField(choices=[('', 'Seleccione')] + list(Cancha.EstadoConservacion.choices))
    tiene_iluminacion     = forms.BooleanField(required=False)
    tiene_cerramiento     = forms.BooleanField(required=False)
    capacidad_espectadores = forms.IntegerField(min_value=0, initial=0)
    observaciones_tecnicas = forms.CharField(widget=forms.Textarea, required=False)

    def clean_nombre_escenario(self):
        nombre = self.cleaned_data.get('nombre_escenario')
        if len(nombre.strip()) < 3:
            raise forms.ValidationError('Mínimo 3 caracteres.')
        return nombre

    def clean_tipo_disciplina(self):
        val = self.cleaned_data.get('tipo_disciplina')
        if not val:
            raise forms.ValidationError('Selecciona un tipo de disciplina.')
        return val

    def clean_tipo_superficie(self):
        val = self.cleaned_data.get('tipo_superficie')
        if not val:
            raise forms.ValidationError('Selecciona un tipo de superficie.')
        return val

    def clean_estado_conservacion(self):
        val = self.cleaned_data.get('estado_conservacion')
        if not val:
            raise forms.ValidationError('Selecciona el estado de conservación.')
        return val


class CargaMasivaCanchasForm(forms.Form):
    archivo = forms.FileField()

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        nombre  = archivo.name.lower()
        if not (nombre.endswith('.xlsx') or nombre.endswith('.csv')):
            raise forms.ValidationError('Solo se permiten archivos .xlsx o .csv')
        if archivo.size > 5 * 1024 * 1024:
            raise forms.ValidationError('El archivo no puede superar 5MB.')
        return archivo