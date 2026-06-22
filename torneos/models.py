from django.db import models
from inscripciones.models import Equipo
from accounts.models import Jugador
from datetime import date


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

    class Formato(models.TextChoices):
        GRUPOS_SOLO    = 'GRUPOS_SOLO',    'Solo fase de grupos (liga)'
        GRUPOS_FINAL   = 'GRUPOS_FINAL',   'Grupos + Final'
        GRUPOS_SEMI    = 'GRUPOS_SEMI',    'Grupos + Semifinales + Final'
        GRUPOS_CUARTOS = 'GRUPOS_CUARTOS', 'Grupos + Cuartos + Semifinales + Final'

    class MotivoCancelacion(models.TextChoices):
        CLIMA = 'CLIMA', 'Clima o estado de la cancha'
        CUPOS = 'CUPOS', 'Cupos insuficientes'
        LOGISTICA = 'LOGISTICA', 'Problemas logisticos'
        SEGURIDAD = 'SEGURIDAD', 'Seguridad'
        OTRO = 'OTRO', 'Otro motivo'

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

    formato = models.CharField(
        max_length=20,
        choices=Formato.choices,
        default=Formato.GRUPOS_SOLO
    )
    fase_actual = models.CharField(
        max_length=15,
        choices=[
            ('GRUPOS',      'Fase de grupos'),
            ('CUARTOS',     'Cuartos de final'),
            ('SEMIFINAL',   'Semifinal'),
            ('TERCER_PUES', 'Tercer puesto'),
            ('FINAL',       'Final'),
        ],
        default='GRUPOS',
        blank=True
    )
    motivo_cancelacion = models.CharField(
        max_length=20,
        choices=MotivoCancelacion.choices,
        blank=True
    )
    motivo_cancelacion_detalle = models.TextField(blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    @property
    def cupos_disponibles(self):
        inscritos = self.inscripciones.filter(estado='ACTIVA').count()
        return self.cupo_maximo - inscritos

    @property
    def puede_inscribirse(self):
        return (
            self.cupos_disponibles > 0
            and self.estado == self.Estado.PROXIMO
            and date.today() < self.fecha_inicio
        )

    def actualizar_estado(self):
        if self.estado == self.Estado.CANCELADO:
            return

        hoy = date.today()

        if hoy < self.fecha_inicio:
            nuevo = self.Estado.PROXIMO
        elif self.fecha_inicio <= hoy <= self.fecha_fin:
            nuevo = self.Estado.EN_CURSO
        else:
            partidos = self.partidos.all()
            pendientes = partidos.exclude(
                estado__in=['FINALIZADO', 'SUSPENDIDO']
            ).count()
            if not partidos.exists() or pendientes == 0:
                nuevo = self.Estado.FINALIZADO
            else:
                nuevo = self.Estado.EN_CURSO

        if self.estado != nuevo:
            self.estado = nuevo
            self.save(update_fields=['estado'])

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

    torneo            = models.ForeignKey(
        Torneo, on_delete=models.CASCADE, related_name='inscripciones'
    )
    equipo            = models.ForeignKey(
        Equipo, on_delete=models.CASCADE, related_name='inscripciones_torneo'
    )
    estado            = models.CharField(
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
        PROGRAMADO = 'PROGRAMADO', 'Programado'
        EN_JUEGO   = 'EN_JUEGO',   'En juego'
        FINALIZADO = 'FINALIZADO', 'Finalizado'
        SUSPENDIDO = 'SUSPENDIDO', 'Suspendido'

    class Fase(models.TextChoices):
        GRUPOS      = 'GRUPOS',      'Fase de grupos'
        CUARTOS     = 'CUARTOS',     'Cuartos de final'
        SEMIFINAL   = 'SEMIFINAL',   'Semifinal'
        TERCER_PUES = 'TERCER_PUES', 'Tercer puesto'
        FINAL       = 'FINAL',       'Final'

    torneo        = models.ForeignKey(
        Torneo, on_delete=models.CASCADE, related_name='partidos'
    )
    equipo_local  = models.ForeignKey(
        Equipo, on_delete=models.CASCADE,
        related_name='partidos_local', null=True, blank=True
    )
    equipo_visita = models.ForeignKey(
        Equipo, on_delete=models.CASCADE,
        related_name='partidos_visita', null=True, blank=True
    )
    fase          = models.CharField(
        max_length=15, choices=Fase.choices, default=Fase.GRUPOS
    )
    fecha         = models.DateTimeField()
    ubicacion     = models.CharField(max_length=200, blank=True)
    goles_local   = models.PositiveIntegerField(default=0)
    goles_visita  = models.PositiveIntegerField(default=0)
    estado        = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.PROGRAMADO
    )
    jornada       = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.torneo.actualizar_estado()

    def __str__(self):
        local  = self.equipo_local.nombre  if self.equipo_local  else 'Por definir'
        visita = self.equipo_visita.nombre if self.equipo_visita else 'Por definir'
        return f'{local} vs {visita} — {self.torneo} ({self.get_fase_display()})'

    class Meta:
        verbose_name = 'Partido'
        verbose_name_plural = 'Partidos'
        ordering = ['fase', 'jornada', 'fecha']


class EstadisticaJugador(models.Model):
    partido            = models.ForeignKey(
        Partido, on_delete=models.CASCADE, related_name='estadisticas'
    )
    jugador            = models.ForeignKey(
        Jugador, on_delete=models.CASCADE, related_name='estadisticas'
    )
    equipo             = models.ForeignKey(
        Equipo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='estadisticas_torneo'
    )
    goles              = models.PositiveIntegerField(default=0)
    asistencias        = models.PositiveIntegerField(default=0)
    tarjetas_amarillas = models.PositiveIntegerField(default=0)
    tarjetas_rojas     = models.PositiveIntegerField(default=0)
    minutos_jugados    = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('partido', 'jugador')
        verbose_name = 'Estadística de Jugador'
        verbose_name_plural = 'Estadísticas de Jugadores'

    def __str__(self):
        return f'{self.jugador} en {self.partido}'
