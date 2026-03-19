from django.urls import path
from .views import register, CustomLoginView
from .forms import CustomPasswordResetForm
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),
    path('registro/admin/',  views.register_admin, name='register_admin'),
    path('dashboard/admin/', views.dashboard_admin, name = 'dashboard_admin'),
    path('dashboard/entrenador/', views.dashboard_entrenador, name = 'dashboard_entrenador'),
    path('dashboard/jugador/', views.dashboard_jugador, name = 'dashboard_jugador'),
    path('perfil/editar/', views.editar_perfil, name = 'editar_perfil'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
    template_name='accounts/recuperar_contra.html',
    form_class=CustomPasswordResetForm,
    email_template_name='accounts/password_reset_email.txt',       # ← texto plano (obligatorio)
    html_email_template_name='accounts/password_reset_email.html', # ← este es el HTML bonito
    subject_template_name='accounts/password_reset_subject.txt',
), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/recuperar_contra_enviado.html'
    ), name='password_reset_done'),
    
    # 3. El link que llega al correo (Formulario de nueva clave)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/nueva_contra_form.html'
    ), name='password_reset_confirm'),
    
    # 4. Mensaje de "Contraseña cambiada con éxito"
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/nueva_contra_listo.html'
    ), name='password_reset_complete'),
]