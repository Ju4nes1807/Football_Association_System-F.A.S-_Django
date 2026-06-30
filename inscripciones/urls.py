from django.urls import path
from . import views

app_name = 'inscripciones'

urlpatterns = [
    path('equipo/registrar/', views.registrar_equipo, name = 'registrar_equipo'),
    path('equipo/<int:equipo_id>/editar/', views.editar_equipo, name='editar_equipo'),
    path('equipo/<int:equipo_id>/eliminar/', views.eliminar_equipo, name='eliminar_equipo'),
    path('equipo/<int:equipo_id>/programar-eliminacion/', views.programar_eliminacion_equipo, name='programar_eliminacion_equipo'),
    path('equipo/lista/', views.lista_equipos, name='lista_equipos'),
    path('equipo/<int:equipo_id>/aprobar/',  views.aprobar_equipo,   name='aprobar_equipo'),
    path('equipo/mi-equipo/', views.mi_equipo, name = 'mi_equipo'),
    path('equipo/<int:equipo_id>/seleccionar/', views.seleccionar_equipo_activo, name='seleccionar_equipo'),
    path('jugadores/', views.lista_jugadores, name='lista_jugadores'),
    path('jugadores/<int:jugador_id>/eliminar/', views.eliminar_jugador, name='eliminar_jugador'),
    path('jugadores/registrar/',views.registrar_jugador, name='registrar_jugador'),
    path('jugadores/carga-masiva/', views.carga_masiva_jugadores, name='carga_masiva_jugadores'),
    path('jugadores/<int:jugador_id>/editar/', views.editar_jugador, name='editar_jugador'),
    # Canchas — admin
    path('canchas/', views.lista_canchas, name='lista_canchas'),
    path('canchas/crear/', views.crear_cancha, name='crear_cancha'),
    path('canchas/<int:cancha_id>/editar/', views.editar_cancha, name='editar_cancha'),
    path('canchas/<int:cancha_id>/eliminar/', views.eliminar_cancha, name='eliminar_cancha'),
    path('canchas/<int:cancha_id>/disponibilidad/', views.cambiar_disponibilidad, name='cambiar_disponibilidad'),
    path('canchas/carga-masiva/', views.carga_masiva_canchas, name='carga_masiva_canchas'),
# Canchas — entrenador
    path('canchas/ver/', views.lista_canchas_entrenador, name='lista_canchas_entrenador'),
    path('api/localidades/',  views.api_localidades, name='api_localidades'),
    path('api/barrios/', views.api_barrios, name='api_barrios'),
]
