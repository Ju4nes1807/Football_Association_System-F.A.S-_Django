from django.urls import path
from . import views


urlpatterns = [
    path('', views.lista_entrenamientos, name='lista_entrenamientos'),
    path('crear/', views.crear_entrenamiento, name='crear_entrenamiento'),
    path('editar/<int:pk>/', views.editar_entrenamiento, name='editar_entrenamiento'),
    path('eliminar/<int:pk>/', views.eliminar_entrenamiento, name='eliminar_entrenamiento'),
    path('entrenamientos/mis-entrenamientos/', views.lista_entrenamientos_jugador, name='lista_entrenamientos_jugador'),
]