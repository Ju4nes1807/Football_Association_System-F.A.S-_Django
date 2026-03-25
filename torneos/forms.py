from django import forms
from datetime import date
from django.db.models import Q
from .models import Torneo, Partido, EstadisticaJugador


class TorneoForm(forms.ModelForm):
    class Meta:
        model = Torneo
        fields = [
            'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin',
            'cupo_maximo', 'categoria', 'ubicacion', 'estado'
        ]
        widgets = {
            'nombre':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del torneo'}),
            'descripcion':  forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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
        self.torneo = torneo
        if torneo:
            from inscripciones.models import Equipo
            equipos_ids = torneo.inscripciones.filter(
                estado='ACTIVA'
            ).values_list('equipo_id', flat=True)
            qs = Equipo.objects.filter(id__in=equipos_ids)
            self.fields['equipo_local'].queryset  = qs
            self.fields['equipo_visita'].queryset = qs

    def clean(self):
        cleaned_data = super().clean()
        local  = cleaned_data.get('equipo_local')
        visita = cleaned_data.get('equipo_visita')
        fecha  = cleaned_data.get('fecha')
        jornada = cleaned_data.get('jornada')

        # Equipos distintos
        if local and visita and local == visita:
            raise forms.ValidationError(
                'El equipo local y el equipo visitante no pueden ser el mismo.'
            )

        # Fecha dentro del rango del torneo
        if self.torneo and fecha:
            fecha_solo = fecha.date() if hasattr(fecha, 'date') else fecha
            if fecha_solo < self.torneo.fecha_inicio or fecha_solo > self.torneo.fecha_fin:
                raise forms.ValidationError(
                    f'La fecha del partido debe estar entre '
                    f'{self.torneo.fecha_inicio.strftime("%d/%m/%Y")} y '
                    f'{self.torneo.fecha_fin.strftime("%d/%m/%Y")}.'
                )

        # No repetir el mismo par de equipos en la misma jornada
        if self.torneo and local and visita and jornada:
            qs = Partido.objects.filter(
                torneo=self.torneo,
                jornada=jornada,
            ).filter(
                models.Q(equipo_local=local, equipo_visita=visita) |
                models.Q(equipo_local=visita, equipo_visita=local)
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
            'jugador':             forms.Select(attrs={'class': 'form-select'}),
            'equipo':              forms.Select(attrs={'class': 'form-select'}),
            'goles':               forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'asistencias':         forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tarjetas_amarillas':  forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tarjetas_rojas':      forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'minutos_jugados':     forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }