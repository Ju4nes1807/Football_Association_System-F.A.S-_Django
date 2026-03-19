from django.urls import path
from . import views

app_name = 'inscripciones'

urlpatterns = [
    # Entrenador
    path('equipo/registrar/', views.registrar_equipo, name = 'registrar_equipo'),
    path('equipo/<int:equipo_id>/editar/', views.editar_equipo, name='editar_equipo'),
    path('equipo/<int:equipo_id>/eliminar/', views.eliminar_equipo, name='eliminar_equipo'),
    path('equipo/lista/', views.lista_equipos, name='lista_equipos'),
    path('equipo/<int:equipo_id>/aprobar/',  views.aprobar_equipo,   name='aprobar_equipo'),
    path('equipo/mi-equipo/', views.mi_equipo, name = 'mi_equipo'),
    path('api/localidades/',  views.api_localidades, name='api_localidades'),
    path('api/barrios/', views.api_barrios, name='api_barrios'),
]