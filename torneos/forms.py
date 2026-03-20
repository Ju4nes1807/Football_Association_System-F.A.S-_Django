from django import forms
from .models import Torneo, Partido, EstadisticaJugador


class TorneoForm(forms.ModelForm):
    class Meta:
        model = Torneo
        fields = [
            'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin',
            'cupo_maximo', 'categoria', 'ubicacion', 'estado'
        ]
        widgets = {
            'nombre':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del torneo'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cupo_maximo':  forms.NumberInput(attrs={'class': 'form-control', 'min': 2}),
            'categoria':    forms.Select(attrs={'class': 'form-select'}),
            'ubicacion':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Parque El Salitre, Bogotá'}),
            'estado':       forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('fecha_inicio')
        fin    = cleaned.get('fecha_fin')
        if inicio and fin and fin < inicio:
            raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        return cleaned


class PartidoForm(forms.ModelForm):
    class Meta:
        model = Partido
        fields = [
            'equipo_local', 'equipo_visita', 'fecha',
            'ubicacion', 'goles_local', 'goles_visita', 'estado', 'jornada'
        ]
        widgets = {
            'equipo_local':  forms.Select(attrs={'class': 'form-select'}),
            'equipo_visita': forms.Select(attrs={'class': 'form-select'}),
            'fecha':         forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'ubicacion':     forms.TextInput(attrs={'class': 'form-control'}),
            'goles_local':   forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'goles_visita':  forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'estado':        forms.Select(attrs={'class': 'form-select'}),
            'jornada':       forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, torneo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if torneo:
            equipos_ids = torneo.inscripciones.filter(
                estado='ACTIVA'
            ).values_list('equipo_id', flat=True)
            from inscripciones.models import Equipo
            self.fields['equipo_local'].queryset  = Equipo.objects.filter(id__in=equipos_ids)
            self.fields['equipo_visita'].queryset = Equipo.objects.filter(id__in=equipos_ids)


class EstadisticaForm(forms.ModelForm):
    class Meta:
        model = EstadisticaJugador
        fields = ['jugador', 'goles', 'asistencias', 'tarjetas_amarillas', 'tarjetas_rojas', 'minutos_jugados']
        widgets = {
            'jugador':             forms.Select(attrs={'class': 'form-select'}),
            'goles':               forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'asistencias':         forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tarjetas_amarillas':  forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tarjetas_rojas':      forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'minutos_jugados':     forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }