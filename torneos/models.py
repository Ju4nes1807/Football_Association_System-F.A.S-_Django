from django.db import models
from inscripciones.models import Equipo
from accounts.models import Jugador


class Torneo(models.Model):

    class Estado(models.TextChoices):
        PROXIMO    = 'PROXIMO',    'Próximo'
        EN_CURSO   = 'EN_CURSO',   'En curso'
        FINALIZADO = 'FINALIZADO', 'Finalizado'
        CANCELADO  = 'CANCELADO',  'Cancelado'

    class Categoria(models.TextChoices):
        SUB8  = 'SUB8',  'Sub-8'
        SUB10 = 'SUB10', 'Sub-10'
        SUB12 = 'SUB12', 'Sub-12'
        SUB14 = 'SUB14', 'Sub-14'
        SUB16 = 'SUB16', 'Sub-16'
        SUB18 = 'SUB18', 'Sub-18'
        MAYOR = 'MAYOR', 'Mayor/Libre'

    nombre         = models.CharField(max_length=100)
    descripcion    = models.TextField(blank=True)
    fecha_inicio   = models.DateField()
    fecha_fin      = models.DateField()
    cupo_maximo    = models.PositiveIntegerField(default=8)
    categoria      = models.CharField(max_length=10, choices=Categoria.choices)
    ubicacion      = models.CharField(max_length=200)
    estado         = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PROXIMO
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    @property
    def cupos_disponibles(self):
        inscritos = self.inscripciones.filter(estado='ACTIVA').count()
        return self.cupo_maximo - inscritos

    @property
    def puede_inscribirse(self):
        from datetime import date
        return (
            self.cupos_disponibles > 0
            and self.estado == self.Estado.PROXIMO
            and date.today() < self.fecha_inicio
        )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Torneo'
        verbose_name_plural = 'Torneos'
        ordering = ['-fecha_creacion']


class InscripcionTorneo(models.Model):

    class Estado(models.TextChoices):
        ACTIVA    = 'ACTIVA',    'Activa'
        CANCELADA = 'CANCELADA', 'Cancelada'

    torneo           = models.ForeignKey(
        Torneo, on_delete=models.CASCADE, related_name='inscripciones'
    )
    equipo           = models.ForeignKey(
        Equipo, on_delete=models.CASCADE, related_name='inscripciones_torneo'
    )
    estado           = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.ACTIVA
    )
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('torneo', 'equipo')
        verbose_name = 'Inscripción a Torneo'
        verbose_name_plural = 'Inscripciones a Torneos'

    def __str__(self):
        return f'{self.equipo} → {self.torneo}'


class Partido(models.Model):

    class Estado(models.TextChoices):
        PROGRAMADO  = 'PROGRAMADO',  'Programado'
        EN_JUEGO    = 'EN_JUEGO',    'En juego'
        FINALIZADO  = 'FINALIZADO',  'Finalizado'
        SUSPENDIDO  = 'SUSPENDIDO',  'Suspendido'

    torneo        = models.ForeignKey(
        Torneo, on_delete=models.CASCADE, related_name='partidos'
    )
    equipo_local  = models.ForeignKey(
        Equipo, on_delete=models.CASCADE, related_name='partidos_local'
    )
    equipo_visita = models.ForeignKey(
        Equipo, on_delete=models.CASCADE, related_name='partidos_visita'
    )
    fecha         = models.DateTimeField()
    ubicacion     = models.CharField(max_length=200, blank=True)
    goles_local   = models.PositiveIntegerField(default=0)
    goles_visita  = models.PositiveIntegerField(default=0)
    estado        = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PROGRAMADO
    )
    jornada       = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.equipo_local} vs {self.equipo_visita} — {self.torneo}'

    class Meta:
        verbose_name = 'Partido'
        verbose_name_plural = 'Partidos'
        ordering = ['fecha']


class EstadisticaJugador(models.Model):
    partido = models.ForeignKey(
        Partido, on_delete=models.CASCADE, related_name='estadisticas'
    )
    jugador = models.ForeignKey(
        Jugador, on_delete=models.CASCADE, related_name='estadisticas'
    )
    goles          = models.PositiveIntegerField(default=0)
    asistencias    = models.PositiveIntegerField(default=0)
    tarjetas_amarillas = models.PositiveIntegerField(default=0)
    tarjetas_rojas     = models.PositiveIntegerField(default=0)
    minutos_jugados    = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('partido', 'jugador')
        verbose_name = 'Estadística de Jugador'
        verbose_name_plural = 'Estadísticas de Jugadores'

    def __str__(self):
        return f'{self.jugador} en {self.partido}'