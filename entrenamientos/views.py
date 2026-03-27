from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Entrenamiento
from .forms import EntrenamientoForm

# --- LISTAR ENTRENAMIENTOS ---
@login_required
def lista_entrenamientos(request):
    user = request.user

    if user.rol == 'ADMIN':
        entrenamientos = Entrenamiento.objects.all()
    elif user.rol == 'ENTRENADOR':
        entrenamientos = Entrenamiento.objects.filter(equipo=user.entrenador.equipo)
    else: # JUGADOR
        entrenamientos = Entrenamiento.objects.filter(equipo=user.jugador.equipo)

    return render(request, 'entrenamientos/lista.html', {'entrenamientos': entrenamientos})

# --- CREAR ENTRENAMIENTO ---
@login_required
def crear_entrenamiento(request):
    # Seguridad: Solo entrenadores crean
    if request.user.rol != 'ENTRENADOR':
        messages.error(request, 'No tienes permisos para crear entrenamientos.')
        return redirect('lista_entrenamientos')

    if request.method == 'POST':
        form = EntrenamientoForm(request.POST)
        if form.is_valid():
            entrenamiento = form.save(commit=False)
            # Asignación automática de datos que no pedimos en el form
            entrenamiento.entrenador = request.user.entrenador
            entrenamiento.equipo = request.user.entrenador.equipo
            entrenamiento.save()
            messages.success(request, '¡Sesión de entrenamiento programada!')
            return redirect('lista_entrenamientos')
    else:
        form = EntrenamientoForm()

    # Apunta a tu nuevo archivo crear.html
    return render(request, 'entrenamientos/crear.html', {'form': form})

# --- EDITAR ENTRENAMIENTO ---
@login_required
def editar_entrenamiento(request, pk):
    entrenamiento = get_object_or_404(Entrenamiento, pk=pk)

    # Seguridad: Solo el dueño o el admin editan
    if request.user.rol != 'ADMIN' and entrenamiento.entrenador != request.user.entrenador:
        messages.error(request, 'No puedes editar un entrenamiento que no creaste.')
        return redirect('lista_entrenamientos')

    if request.method == 'POST':
        form = EntrenamientoForm(request.POST, instance=entrenamiento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entrenamiento actualizado correctamente.')
            return redirect('lista_entrenamientos')
    else:
        form = EntrenamientoForm(instance=entrenamiento)

    # Apunta a tu nuevo archivo editar.html
    return render(request, 'entrenamientos/editar.html', {'form': form})

# --- ELIMINAR ENTRENAMIENTO ---
@login_required
def eliminar_entrenamiento(request, pk):
    entrenamiento = get_object_or_404(Entrenamiento, pk=pk)

    if request.user.rol != 'ADMIN' and entrenamiento.entrenador != request.user.entrenador:
        messages.error(request, 'Permiso denegado para eliminar.')
        return redirect('lista_entrenamientos')

    if request.method == 'POST':
        entrenamiento.delete()
        messages.success(request, 'El entrenamiento ha sido eliminado.')
    
    return redirect('lista_entrenamientos')
@login_required
def lista_entrenamientos_jugador(request):
  
    if request.user.rol != 'JUGADOR':
        return redirect('dashboard_entrenador')
    
  
    entrenamientos = Entrenamiento.objects.all().order_by('fecha_hora')
    
    return render(request, 'entrenamientos/lista_jugador.html', {
        'entrenamientos': entrenamientos
    })