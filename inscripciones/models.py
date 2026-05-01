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
    _motivo_rechazo = models.TextField(db_column='motivo_rechazo', blank=True, null=True)
    _fecha_rechazo = models.DateTimeField(db_column='fecha_rechazo', blank=True, null=True)
    _bloqueado_hasta = models.DateTimeField(db_column='bloqueado_hasta', blank=True, null=True)
    _eliminar_programada_para = models.DateTimeField(db_column='eliminar_programada_para', blank=True, null=True)
    _motivo_eliminacion = models.TextField(db_column='motivo_eliminacion', blank=True, null=True)
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
    
    @property
    def motivo_rechazo(self):
        return self._motivo_rechazo

    @motivo_rechazo.setter
    def motivo_rechazo(self, value):
        self._motivo_rechazo = value.strip() if value else None

    @property
    def fecha_rechazo(self):
        return self._fecha_rechazo

    @fecha_rechazo.setter
    def fecha_rechazo(self, value):
        self._fecha_rechazo = value

    @property
    def bloqueado_hasta(self):
        return self._bloqueado_hasta

    @bloqueado_hasta.setter
    def bloqueado_hasta(self, value):
        self._bloqueado_hasta = value

    @property
    def eliminar_programada_para(self):
        return self._eliminar_programada_para

    @eliminar_programada_para.setter
    def eliminar_programada_para(self, value):
        self._eliminar_programada_para = value

    @property
    def motivo_eliminacion(self):
        return self._motivo_eliminacion

    @motivo_eliminacion.setter
    def motivo_eliminacion(self, value):
        clean = value.strip() if value else ''
        self._motivo_eliminacion = clean or None

    def __str__(self): return self._nombre

    class Meta:
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'

class Cancha(models.Model):
    class TipoDisciplina(models.TextChoices):
        FUTBOL_11 = 'FUTBOL_11', 'Futbol 11'
        FUTBOL_8 = 'FUTBOL_8', 'Futbol 8'
        FUTBOL_5 = 'FUTBOL_5', 'Futbol 5'
        MICROFUTBOL = 'MICROFUTBOL', 'Microfútbol'
    
    class TipoSuperficie(models.TextChoices):
        SINTETICA = 'SINTETICA', 'Sintetica'
        NATURAL = 'NATURAL', 'Natural'
        ARENA = 'ARENA', 'Arena'
        CEMENTO = 'CEMENTO', 'Cemento (Dura)'
    
    class EstadoConservacion(models.TextChoices):
        BUENO = 'BUENO', 'Bueno'
        REGULAR = 'REGULAR', 'Regular'
        MALO = 'MALO', 'Malo'
        CRITICO = 'CRITICO', 'Critico'
    
    class Disponibilidad(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        OCUPADA = 'OCUPADA', 'Ocupada'
        MANTENIMIENTO = 'MANTENIMIENTO', 'En Mantenimiento'
        FUERA_SERVICIO = 'FUERA_SERVICIO', 'Fuera de servicio'
    
    _codigo_idrd          = models.CharField(max_length=50, blank=True, null=True, db_column='codigo_idrd')
    _nombre_escenario     = models.CharField(max_length=150, db_column='nombre_escenario')
    _localidad            = models.CharField(max_length=100, db_column='localidad')
    _barrio               = models.CharField(max_length=100, db_column='barrio')
    _direccion_exacta     = models.CharField(max_length=200, db_column='direccion_exacta')
    _codigo_rupi          = models.CharField(max_length=50, blank=True, null=True, db_column='codigo_rupi')
    _tipo_disciplina      = models.CharField(max_length=20, choices=TipoDisciplina.choices, db_column='tipo_disciplina')
    _tipo_superficie      = models.CharField(max_length=20, choices=TipoSuperficie.choices, db_column='tipo_superficie')
    _medidas_area         = models.CharField(max_length=50, db_column='medidas_area')
    _estado_conservacion  = models.CharField(max_length=10, choices=EstadoConservacion.choices, db_column='estado_conservacion')
    _tiene_iluminacion    = models.BooleanField(default=False, db_column='tiene_iluminacion')
    _tiene_cerramiento    = models.BooleanField(default=False, db_column='tiene_cerramiento')
    _capacidad_espectadores = models.PositiveIntegerField(default=0, db_column='capacidad_espectadores')
    _observaciones_tecnicas = models.TextField(blank=True, null=True, db_column='observaciones_tecnicas')
    _disponibilidad       = models.CharField(max_length=20, choices=Disponibilidad.choices, default=Disponibilidad.DISPONIBLE, db_column='disponibilidad')
    _latitud = models.FloatField(null = True, blank = True)
    _longitud = models.FloatField(null = True, blank = True)
    fecha_registro        = models.DateTimeField(auto_now_add=True)

    # ── Getters y Setters ──
    @property
    def codigo_idrd(self): return self._codigo_idrd
    @codigo_idrd.setter
    def codigo_idrd(self, value): self._codigo_idrd = value.strip() if value else None

    @property
    def nombre_escenario(self): return self._nombre_escenario
    @nombre_escenario.setter
    def nombre_escenario(self, value):
        if not value or len(value.strip()) < 3:
            raise ValueError('El nombre debe tener al menos 3 caracteres.')
        self._nombre_escenario = value.strip()

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
    def direccion_exacta(self): return self._direccion_exacta
    @direccion_exacta.setter
    def direccion_exacta(self, value):
        if not value or not value.strip():
            raise ValueError('La dirección es obligatoria.')
        self._direccion_exacta = value.strip()

    @property
    def codigo_rupi(self): return self._codigo_rupi
    @codigo_rupi.setter
    def codigo_rupi(self, value): self._codigo_rupi = value.strip() if value else None

    @property
    def tipo_disciplina(self): return self._tipo_disciplina
    @tipo_disciplina.setter
    def tipo_disciplina(self, value):
        if value not in [c[0] for c in self.TipoDisciplina.choices]:
            raise ValueError('Tipo de disciplina inválido.')
        self._tipo_disciplina = value

    @property
    def tipo_superficie(self): return self._tipo_superficie
    @tipo_superficie.setter
    def tipo_superficie(self, value):
        if value not in [c[0] for c in self.TipoSuperficie.choices]:
            raise ValueError('Tipo de superficie inválido.')
        self._tipo_superficie = value

    @property
    def medidas_area(self): return self._medidas_area
    @medidas_area.setter
    def medidas_area(self, value):
        if not value or not value.strip():
            raise ValueError('Las medidas son obligatorias.')
        self._medidas_area = value.strip()

    @property
    def estado_conservacion(self): return self._estado_conservacion
    @estado_conservacion.setter
    def estado_conservacion(self, value):
        if value not in [c[0] for c in self.EstadoConservacion.choices]:
            raise ValueError('Estado de conservación inválido.')
        self._estado_conservacion = value

    @property
    def tiene_iluminacion(self): return self._tiene_iluminacion
    @tiene_iluminacion.setter
    def tiene_iluminacion(self, value): self._tiene_iluminacion = bool(value)

    @property
    def tiene_cerramiento(self): return self._tiene_cerramiento
    @tiene_cerramiento.setter
    def tiene_cerramiento(self, value): self._tiene_cerramiento = bool(value)

    @property
    def capacidad_espectadores(self): return self._capacidad_espectadores
    @capacidad_espectadores.setter
    def capacidad_espectadores(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError('La capacidad debe ser un número positivo.')
        self._capacidad_espectadores = value

    @property
    def observaciones_tecnicas(self): return self._observaciones_tecnicas
    @observaciones_tecnicas.setter
    def observaciones_tecnicas(self, value):
        self._observaciones_tecnicas = value.strip() if value else None

    @property
    def disponibilidad(self): return self._disponibilidad
    @disponibilidad.setter
    def disponibilidad(self, value):
        if value not in [d[0] for d in self.Disponibilidad.choices]:
            raise ValueError('Disponibilidad inválida.')
        self._disponibilidad = value
    
    @property
    def latitud(self):
        return self._latitud
    @latitud.setter
    def latitud(self, v):
        self._latitud = v
    
    @property
    def longitud(self): return self._longitud
    @longitud.setter
    def longitud(self, v): self._longitud = v

    # Propiedades para templates
    @property
    def disponibilidad_display(self): return self.get__disponibilidad_display()
    @property
    def tipo_disciplina_display(self): return self.get__tipo_disciplina_display()
    @property
    def tipo_superficie_display(self): return self.get__tipo_superficie_display()
    @property
    def estado_conservacion_display(self): return self.get__estado_conservacion_display()

    def __str__(self): return self._nombre_escenario

    class Meta:
        verbose_name = 'Cancha'
        verbose_name_plural = 'Canchas'
        ordering = ['_nombre_escenario']