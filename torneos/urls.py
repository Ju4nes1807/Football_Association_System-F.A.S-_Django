from django.urls import path
from . import views

app_name = 'torneos'

urlpatterns = [
    # Admin — torneos
    path('admin/',                                     views.admin_lista_torneos,       name='admin_lista_torneos'),
    path('admin/crear/',                               views.admin_crear_torneo,        name='admin_crear_torneo'),
    path('admin/<int:torneo_id>/editar/',              views.admin_editar_torneo,       name='admin_editar_torneo'),
    path('admin/<int:torneo_id>/eliminar/',            views.admin_eliminar_torneo,     name='admin_eliminar_torneo'),
    path('admin/<int:torneo_id>/detalle/',             views.admin_detalle_torneo,      name='admin_detalle_torneo'),
    # Admin — partidos
    path('admin/<int:torneo_id>/partido/crear/',       views.admin_crear_partido,       name='admin_crear_partido'),
    path('admin/partido/<int:partido_id>/editar/',     views.admin_editar_partido,      name='admin_editar_partido'),
    # Admin — inscripciones
    path('admin/desinscribir/<int:inscripcion_id>/',   views.admin_desinscribir_equipo, name='admin_desinscribir'),
    # Admin — fases
    path('admin/<int:torneo_id>/fixture/',             views.admin_generar_fixture,     name='admin_generar_fixture'),
    path('admin/<int:torneo_id>/cuartos/',             views.admin_generar_cuartos,     name='admin_generar_cuartos'),
    path('admin/<int:torneo_id>/semifinales/',         views.admin_generar_semifinales, name='admin_generar_semifinales'),
    path('admin/<int:torneo_id>/final/',               views.admin_generar_final,       name='admin_generar_final'),
    # Entrenador
    path('entrenador/',                                views.entrenador_lista_torneos,        name='entrenador_lista_torneos'),
    path('entrenador/<int:torneo_id>/inscribir/',      views.entrenador_inscribir,            name='entrenador_inscribir'),
    path('entrenador/cancelar/<int:inscripcion_id>/',  views.entrenador_cancelar_inscripcion, name='entrenador_cancelar'),
    path('entrenador/<int:torneo_id>/mis-partidos/',   views.entrenador_mis_partidos,         name='entrenador_mis_partidos'),
    path('entrenador/partido/<int:partido_id>/estadisticas/', views.entrenador_estadisticas_partido, name='entrenador_estadisticas_partido'),
    # Jugador
    path('jugador/mis-torneos/',                       views.jugador_mis_torneos,             name='jugador_mis_torneos'),
    path('jugador/mis-torneos/datos/',                 views.jugador_mis_torneos_datos,       name='jugador_mis_torneos_datos'),
]
