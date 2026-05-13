import re
from datetime import date

from django import forms
from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat
from .models import Torneo, Partido, EstadisticaJugador
from inscripciones.models import Cancha


CUPO_MINIMO = 6
CUPOS_PARES = range(CUPO_MINIMO, 24, 2)
CUPOS_CHOICES = (
    [('', 'Seleccione la cantidad de cupos')]
    + [(str(cupo), f'{cupo} equipos') for cupo in CUPOS_PARES]
    + [('OTRO', 'Otro numero par')]
)


class TorneoForm(forms.ModelForm):
    formato = forms.ChoiceField(
        choices=[('', 'Seleccione un formato de torneo')] + list(Torneo.Formato.choices),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cupo_maximo = forms.ChoiceField(
        choices=CUPOS_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cupo_personalizado = forms.IntegerField(
        required=False,
        min_value=CUPO_MINIMO,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': CUPO_MINIMO,
            'step': 2,
            'placeholder': 'Ej: 18'
        })
    )

    class Meta:
        model = Torneo
        fields = [
            'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin',
            'cupo_maximo', 'categoria', 'formato', 'ubicacion', 'estado'
        ]
        widgets = {
            'nombre':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del torneo'}),
            'descripcion':  forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'categoria':    forms.Select(attrs={'class': 'form-select'}),
            'ubicacion':    forms.HiddenInput(),
            'estado':       forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cupo_actual = self.instance.cupo_maximo if self.instance and self.instance.pk else None

        if cupo_actual:
            cupo_actual = str(cupo_actual)
            cupos_validos = {str(cupo) for cupo in CUPOS_PARES}
            if cupo_actual in cupos_validos:
                self.initial.setdefault('cupo_maximo', cupo_actual)
            else:
                self.initial.setdefault('cupo_maximo', 'OTRO')
                self.initial.setdefault('cupo_personalizado', self.instance.cupo_maximo)

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()

        if not nombre:
            raise forms.ValidationError('El nombre del torneo es obligatorio.')
        if len(nombre) < 3:
            raise forms.ValidationError('El nombre debe tener al menos 3 caracteres.')
        if not re.match(r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .\'-]+$', nombre):
            raise forms.ValidationError('Usa solo letras, numeros, espacios, puntos, guiones o apostrofes.')

        qs = Torneo.objects.filter(nombre__iexact=nombre)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un torneo con este nombre.')

        return nombre

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()
        if len(descripcion) > 500:
            raise forms.ValidationError('La descripcion no puede superar 500 caracteres.')
        return descripcion

    def clean_ubicacion(self):
        ubicacion = (self.cleaned_data.get('ubicacion') or '').strip()

        if not ubicacion:
            raise forms.ValidationError('Debes seleccionar una cancha disponible.')

        existe_cancha_disponible = Cancha.objects.filter(
            _disponibilidad=Cancha.Disponibilidad.DISPONIBLE
        ).annotate(
            ubicacion_torneo=Concat(
                '_nombre_escenario',
                Value(' - '),
                '_direccion_exacta',
                output_field=CharField()
            )
        ).filter(ubicacion_torneo=ubicacion).exists()

        if not existe_cancha_disponible:
            raise forms.ValidationError('Selecciona una cancha marcada como disponible.')

        return ubicacion

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('fecha_inicio')
        fin    = cleaned.get('fecha_fin')
        formato = cleaned.get('formato')
        cupo_maximo = cleaned.get('cupo_maximo')
        cupo_personalizado = cleaned.get('cupo_personalizado')

        if inicio and not self.instance.pk and inicio < date.today():
            self.add_error('fecha_inicio', 'La fecha de inicio no puede ser anterior a hoy.')

        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha de fin debe ser posterior o igual a la fecha de inicio.')

        if not formato:
            self.add_error('formato', 'Debes seleccionar un formato de torneo.')

        if cupo_maximo == 'OTRO':
            if formato != Torneo.Formato.GRUPOS_SOLO:
                self.add_error('cupo_maximo', 'Solo la liga permite modificar manualmente los cupos.')
            elif cupo_personalizado is None:
                self.add_error('cupo_personalizado', 'Indica un numero par mayor a 4.')
            elif cupo_personalizado % 2 != 0:
                self.add_error('cupo_personalizado', 'El cupo debe ser un numero par.')
            else:
                cleaned['cupo_maximo'] = cupo_personalizado
        elif cupo_maximo:
            cleaned['cupo_maximo'] = int(cupo_maximo)
        else:
            self.add_error('cupo_maximo', 'Debes seleccionar la cantidad de cupos.')

        return cleaned


class PartidoForm(forms.ModelForm):
    class Meta:
        model = Partido
        fields = [
            'equipo_local', 'equipo_visita', 'fase', 'fecha',
            'ubicacion', 'goles_local', 'goles_visita', 'estado', 'jornada'
        ]
        widgets = {
            'equipo_local':  forms.Select(attrs={'class': 'form-select'}),
            'equipo_visita': forms.Select(attrs={'class': 'form-select'}),
            'fase':          forms.Select(attrs={'class': 'form-select'}),
            'fecha':         forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'ubicacion':     forms.TextInput(attrs={'class': 'form-control'}),
            'goles_local':   forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'goles_visita':  forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'estado':        forms.Select(attrs={'class': 'form-select'}),
            'jornada':       forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, torneo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.torneo = torneo
        if torneo:
            from inscripciones.models import Equipo
            equipos_ids = torneo.inscripciones.filter(
                estado='ACTIVA'
            ).values_list('equipo_id', flat=True)
            qs = Equipo.objects.filter(id__in=equipos_ids)
            self.fields['equipo_local'].queryset  = qs
            self.fields['equipo_visita'].queryset = qs
            self.fields['equipo_local'].required  = False
            self.fields['equipo_visita'].required = False

    def clean(self):
        cleaned_data = super().clean()
        local   = cleaned_data.get('equipo_local')
        visita  = cleaned_data.get('equipo_visita')
        fecha   = cleaned_data.get('fecha')
        jornada = cleaned_data.get('jornada')
        fase    = cleaned_data.get('fase')

        if local and visita and local == visita:
            raise forms.ValidationError(
                'El equipo local y el equipo visitante no pueden ser el mismo.'
            )

        if self.torneo and fecha:
            fecha_solo = fecha.date() if hasattr(fecha, 'date') else fecha
            if fecha_solo < self.torneo.fecha_inicio or fecha_solo > self.torneo.fecha_fin:
                raise forms.ValidationError(
                    f'La fecha debe estar entre '
                    f'{self.torneo.fecha_inicio.strftime("%d/%m/%Y")} y '
                    f'{self.torneo.fecha_fin.strftime("%d/%m/%Y")}.'
                )

        if self.torneo and local and visita and jornada and fase == 'GRUPOS':
            qs = Partido.objects.filter(
                torneo=self.torneo,
                fase='GRUPOS',
                jornada=jornada,
            ).filter(
                Q(equipo_local=local, equipo_visita=visita) |
                Q(equipo_local=visita, equipo_visita=local)
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f'Estos equipos ya tienen un partido en la jornada {jornada}.'
                )

        return cleaned_data


class EstadisticaForm(forms.ModelForm):
    class Meta:
        model = EstadisticaJugador
        fields = [
            'jugador', 'equipo', 'goles', 'asistencias',
            'tarjetas_amarillas', 'tarjetas_rojas', 'minutos_jugados'
        ]
        widgets = {
            'jugador':            forms.Select(attrs={'class': 'form-select'}),
            'equipo':             forms.Select(attrs={'class': 'form-select'}),
            'goles':              forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'asistencias':        forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tarjetas_amarillas': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tarjetas_rojas':     forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'minutos_jugados':    forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
