from django.db import models
from accounts.models import Entrenador 
from inscripciones.models import Equipo 

class Entrenamiento(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la sesión")
    descripcion = models.TextField(blank=True, null=True)
    fecha_hora = models.DateTimeField(verbose_name="Fecha y Hora")
    lugar = models.CharField(max_length=150)
    
    # Relaciones
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='entrenamientos')
    entrenador = models.ForeignKey(Entrenador, on_delete=models.CASCADE, related_name='mis_entrenamientos')

    class Meta:
        verbose_name = "Entrenamiento"
        verbose_name_plural = "Entrenamientos"
        ordering = ['fecha_hora']

    def __str__(self):
        return f"{self.nombre} - {self.equipo}"

