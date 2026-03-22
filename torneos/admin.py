from django.contrib import admin
from .models import Torneo, InscripcionTorneo, Partido, EstadisticaJugador

admin.site.register(Torneo)
admin.site.register(InscripcionTorneo)
admin.site.register(Partido)
admin.site.register(EstadisticaJugador)