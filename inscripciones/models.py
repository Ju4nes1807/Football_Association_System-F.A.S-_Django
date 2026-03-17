from django.db import models
from accounts.models import Entrenador


class Equipo(models.Model):

    class Estado(models.TextChoices):
        ESPERA    = 'ESPERA',    'En espera'
        APROBADO  = 'APROBADO',  'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    class Categoria(models.TextChoices):
        SUB8  = 'SUB8',  'Sub-8'
        SUB10 = 'SUB10', 'Sub-10'
        SUB12 = 'SUB12', 'Sub-12'
        SUB14 = 'SUB14', 'Sub-14'
        SUB16 = 'SUB16', 'Sub-16'
        SUB18 = 'SUB18', 'Sub-18'
        MAYOR = 'MAYOR', 'Mayor/Libre'

    _nombre         = models.CharField(max_length=100, unique=True, db_column='nombre')
    _descripcion    = models.TextField(db_column='descripcion', blank=True)
    _anio_fundacion = models.PositiveIntegerField(db_column='anio_fundacion')
    _logo           = models.ImageField(upload_to='equipos/logos/', db_column='logo', blank=True, null=True)
    _categoria      = models.CharField(max_length=10, choices=Categoria.choices, db_column='categoria')
    _localidad      = models.CharField(max_length=100, db_column='localidad')
    _barrio         = models.CharField(max_length=100, db_column='barrio')
    _estado         = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ESPERA, db_column='estado')
    entrenador      = models.OneToOneField(Entrenador, on_delete=models.CASCADE, related_name='equipo')
    fecha_registro  = models.DateTimeField(auto_now_add=True)

    # ── Getters y Setters ──
    @property
    def nombre(self): return self._nombre
    @nombre.setter
    def nombre(self, value):
        if not value or len(value.strip()) < 3:
            raise ValueError('El nombre debe tener al menos 3 caracteres.')
        self._nombre = value.strip()

    @property
    def descripcion(self): return self._descripcion
    @descripcion.setter
    def descripcion(self, value):
        self._descripcion = value.strip() if value else ''

    @property
    def anio_fundacion(self): return self._anio_fundacion
    @anio_fundacion.setter
    def anio_fundacion(self, value):
        from datetime import date
        if not isinstance(value, int) or value < 1900 or value > date.today().year:
            raise ValueError(f'Año inválido. Entre 1900 y {date.today().year}.')
        self._anio_fundacion = value

    @property
    def categoria(self): return self._categoria
    @categoria.setter
    def categoria(self, value):
        if value not in [c[0] for c in self.Categoria.choices]:
            raise ValueError('Categoría inválida.')
        self._categoria = value

    @property
    def localidad(self): return self._localidad
    @localidad.setter
    def localidad(self, value):
        if not value or not value.strip():
            raise ValueError('La localidad es obligatoria.')
        self._localidad = value.strip()

    @property
    def barrio(self): return self._barrio
    @barrio.setter
    def barrio(self, value):
        if not value or not value.strip():
            raise ValueError('El barrio es obligatorio.')
        self._barrio = value.strip()

    @property
    def estado(self): return self._estado
    @estado.setter
    def estado(self, value):
        if value not in [e[0] for e in self.Estado.choices]:
            raise ValueError('Estado inválido.')
        self._estado = value
    
    @property
    def logo(self):
        return self._logo

    @logo.setter
    def logo(self, value):
        self._logo = value

    @property
    def estado_display(self):
        return self.get__estado_display()

    @property
    def categoria_display(self):
        return self.get__categoria_display()

    def __str__(self): return self._nombre

    class Meta:
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'