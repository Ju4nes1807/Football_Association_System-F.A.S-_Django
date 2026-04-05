from django.db import models
from accounts.models import Entrenador 
from inscripciones.models import Equipo, Cancha

class Entrenamiento(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la sesión")
    descripcion = models.TextField(blank=True, null=True)
    fecha_hora = models.DateTimeField(verbose_name="Fecha y Hora")
    lugar = models.CharField(max_length=150)
    cancha = models.ForeignKey(
        Cancha,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entrenamientos_programados'
    )
    
    # Relaciones
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='entrenamientos')
    entrenador = models.ForeignKey(Entrenador, on_delete=models.CASCADE, related_name='mis_entrenamientos')

    class Meta:
        verbose_name = "Entrenamiento"
        verbose_name_plural = "Entrenamientos"
        ordering = ['fecha_hora']

    def __str__(self):
        return f"{self.nombre} - {self.equipo}"

    @property
    def lugar_detallado(self):
        if self.cancha:
            return f"{self.cancha.nombre_escenario} - {self.cancha.direccion_exacta}"
        return self.lugar

