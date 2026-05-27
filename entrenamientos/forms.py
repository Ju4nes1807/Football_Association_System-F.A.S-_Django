from django import forms
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from inscripciones.models import Cancha
from torneos.models import Partido

from .models import Entrenamiento


def _normalizar_texto(valor):
    return (valor or '').strip().lower()


def obtener_canchas_disponibles(fecha_hora=None, entrenamiento=None):
    qs = Cancha.objects.filter(
        _disponibilidad=Cancha.Disponibilidad.DISPONIBLE
    ).order_by('_nombre_escenario')

    if not fecha_hora:
        if entrenamiento and entrenamiento.cancha_id:
            return (qs | Cancha.objects.filter(pk=entrenamiento.cancha_id)).distinct()
        return qs

    ubicaciones_ocupadas = {
        _normalizar_texto(partido.ubicacion)
        for partido in Partido.objects.filter(fecha=fecha_hora).exclude(ubicacion__exact='')
        if _normalizar_texto(partido.ubicacion)
    }

    entrenamientos_qs = Entrenamiento.objects.filter(
        fecha_hora=fecha_hora,
        cancha__isnull=False,
    )
    if entrenamiento and entrenamiento.pk:
        entrenamientos_qs = entrenamientos_qs.exclude(pk=entrenamiento.pk)
    canchas_ocupadas_ids = set(entrenamientos_qs.values_list('cancha_id', flat=True))

    canchas_ids = []
    for cancha in qs:
        if _normalizar_texto(cancha.nombre_escenario) in ubicaciones_ocupadas:
            continue
        if cancha.pk in canchas_ocupadas_ids:
            continue
        canchas_ids.append(cancha.pk)

    if entrenamiento and entrenamiento.cancha_id:
        canchas_ids.append(entrenamiento.cancha_id)

    return Cancha.objects.filter(pk__in=set(canchas_ids)).order_by('_nombre_escenario')


class EntrenamientoForm(forms.ModelForm):
    cancha = forms.ModelChoiceField(
        queryset=Cancha.objects.none(),
        empty_label='Selecciona una cancha disponible',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Entrenamiento
        fields = ['nombre', 'cancha', 'fecha_hora', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Circuito de definicion y presion alta',
                'maxlength': '100'
            }),
            'fecha_hora': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe brevemente los objetivos de la sesion...'
            }),
        }

    def __init__(self, *args, fecha_hora=None, **kwargs):
        super().__init__(*args, **kwargs)
        fecha_base = fecha_hora

        if not fecha_base and self.is_bound:
            fecha_base = parse_datetime(self.data.get('fecha_hora', ''))
        if not fecha_base and self.instance and self.instance.pk:
            fecha_base = self.instance.fecha_hora

        self.fields['cancha'].queryset = obtener_canchas_disponibles(
            fecha_hora=fecha_base,
            entrenamiento=self.instance if self.instance and self.instance.pk else None,
        )

    def clean_fecha_hora(self):
        fecha = self.cleaned_data.get('fecha_hora')
        if fecha and fecha < timezone.now():
            raise forms.ValidationError('No puedes programar un entrenamiento para una fecha que ya paso.')
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        fecha_hora = cleaned_data.get('fecha_hora')
        cancha = cleaned_data.get('cancha')

        if cancha and fecha_hora:
            disponibles = obtener_canchas_disponibles(
                fecha_hora=fecha_hora,
                entrenamiento=self.instance if self.instance and self.instance.pk else None,
            )
            if not disponibles.filter(pk=cancha.pk).exists():
                self.add_error(
                    'cancha',
                    'La cancha seleccionada ya no esta disponible para esa fecha y hora.'
                )

        if cancha:
            cleaned_data['lugar'] = cancha.nombre_escenario

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        cancha = self.cleaned_data.get('cancha')
        if cancha:
            instance.lugar = cancha.nombre_escenario
        if commit:
            instance.save()
        return instance
