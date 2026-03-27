from django import forms
from .models import Entrenamiento
from django.utils import timezone

class EntrenamientoForm(forms.ModelForm):
    class Meta:
        model = Entrenamiento
        # Estos son los campos que el entrenador debe llenar
        fields = ['nombre', 'lugar', 'fecha_hora', 'descripcion']
        
        # Aquí es donde ocurre la magia de Bootstrap
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Entrenamiento de técnica individual'
            }),
            'lugar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cancha Sintética #2'
            }),
            'fecha_hora': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local' # Esto abre el calendario y reloj de Windows/Chrome
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe brevemente los objetivos de la sesión...'
            }),
        }

    # Validación extra para que no agenden entrenamientos en el pasado
    def clean_fecha_hora(self):
        fecha = self.cleaned_data.get('fecha_hora')
        if fecha and fecha < timezone.now():
            raise forms.ValidationError("No puedes programar un entrenamiento para una fecha que ya pasó.")
        return fecha