from django.urls import path
from . import views

app_name = 'inscripciones'

urlpatterns = [
    # Entrenador
    path('equipo/registrar/', views.registrar_equipo, name = 'registrar_equipo'),
    path('equipo/mi-equipo/', views.mi_equipo, name = 'mi_equipo'),
    path('api/localidades/',  views.api_localidades, name='api_localidades'),
    path('api/barrios/', views.api_barrios, name='api_barrios'),
]