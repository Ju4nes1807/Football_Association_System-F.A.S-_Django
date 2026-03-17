from datetime import date
from .models import Equipo
from django import forms

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