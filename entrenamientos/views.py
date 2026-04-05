from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_datetime

from .forms import EntrenamientoForm, obtener_canchas_disponibles
from .models import Entrenamiento


@login_required
def lista_entrenamientos(request):
    user = request.user

    if user.rol == 'ADMIN':
        entrenamientos = Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').all()
    elif user.rol == 'ENTRENADOR':
        entrenamientos = Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').filter(
            equipo=user.entrenador.equipo
        )
    else:
        entrenamientos = Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').filter(
            equipo=user.jugador.equipo
        )

    return render(request, 'entrenamientos/lista.html', {'entrenamientos': entrenamientos})


@login_required
def crear_entrenamiento(request):
    if request.user.rol != 'ENTRENADOR':
        messages.error(request, 'No tienes permisos para crear entrenamientos.')
        return redirect('lista_entrenamientos')

    equipo = getattr(request.user.entrenador, 'equipo', None)
    if not equipo:
        messages.error(request, 'Primero debes tener un equipo asignado para programar entrenamientos.')
        return redirect('dashboard_entrenador')

    fecha_hora = parse_datetime(request.POST.get('fecha_hora', '')) if request.method == 'POST' else None

    if request.method == 'POST':
        form = EntrenamientoForm(request.POST, fecha_hora=fecha_hora)
        if form.is_valid():
            entrenamiento = form.save(commit=False)
            entrenamiento.entrenador = request.user.entrenador
            entrenamiento.equipo = equipo
            entrenamiento.save()
            messages.success(request, 'Sesion de entrenamiento programada correctamente.')
            return redirect('lista_entrenamientos')
    else:
        form = EntrenamientoForm()

    return render(request, 'entrenamientos/crear.html', {
        'form': form,
        'equipo': equipo,
        'modo_edicion': False,
    })


@login_required
def editar_entrenamiento(request, pk):
    entrenamiento = get_object_or_404(
        Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha'),
        pk=pk
    )

    if request.user.rol != 'ADMIN' and entrenamiento.entrenador != request.user.entrenador:
        messages.error(request, 'No puedes editar un entrenamiento que no creaste.')
        return redirect('lista_entrenamientos')

    fecha_hora = parse_datetime(request.POST.get('fecha_hora', '')) if request.method == 'POST' else entrenamiento.fecha_hora

    if request.method == 'POST':
        form = EntrenamientoForm(request.POST, instance=entrenamiento, fecha_hora=fecha_hora)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entrenamiento actualizado correctamente.')
            return redirect('lista_entrenamientos')
    else:
        form = EntrenamientoForm(instance=entrenamiento, fecha_hora=entrenamiento.fecha_hora)

    return render(request, 'entrenamientos/editar.html', {
        'form': form,
        'entrenamiento': entrenamiento,
        'equipo': entrenamiento.equipo,
        'modo_edicion': True,
    })


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
def canchas_disponibles(request):
    if request.user.rol not in ['ENTRENADOR', 'ADMIN']:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    fecha_hora = parse_datetime(request.GET.get('fecha_hora', ''))
    entrenamiento_id = request.GET.get('entrenamiento_id')
    entrenamiento = None

    if entrenamiento_id:
        entrenamiento = get_object_or_404(Entrenamiento, pk=entrenamiento_id)

    canchas = obtener_canchas_disponibles(fecha_hora=fecha_hora, entrenamiento=entrenamiento)
    return JsonResponse({
        'canchas': [
            {
                'id': cancha.id,
                'nombre': cancha.nombre_escenario,
                'direccion': cancha.direccion_exacta,
                'localidad': cancha.localidad,
                'barrio': cancha.barrio,
                'disciplina': cancha.tipo_disciplina_display,
            }
            for cancha in canchas
        ]
    })


@login_required
def lista_entrenamientos_jugador(request):
    if request.user.rol != 'JUGADOR':
        return redirect('dashboard_entrenador')

    jugador = getattr(request.user, 'jugador', None)
    equipo = getattr(jugador, 'equipo', None)
    entrenamientos = Entrenamiento.objects.none()

    if equipo:
        entrenamientos = Entrenamiento.objects.select_related(
            'equipo', 'entrenador', 'cancha'
        ).filter(equipo=equipo).order_by('fecha_hora')

    return render(request, 'entrenamientos/lista_jugador.html', {
        'entrenamientos': entrenamientos,
        'equipo': equipo,
        'jugador': jugador,
    })
