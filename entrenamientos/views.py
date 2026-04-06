import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_datetime

from accounts.models import Jugador
from .forms import EntrenamientoForm, obtener_canchas_disponibles
from .models import AsistenciaEntrenamiento, Entrenamiento


def _obtener_equipo_entrenador(user):
    entrenador = getattr(user, 'entrenador', None)
    if not entrenador:
        return None

    try:
        return entrenador.equipo
    except Exception:
        return None


def _serializar_entrenamientos_mapa(entrenamientos):
    entrenamientos_mapa = []
    for entrenamiento in entrenamientos:
        cancha = entrenamiento.cancha
        if not cancha or cancha.latitud is None or cancha.longitud is None:
            continue

        entrenamientos_mapa.append({
            'id': entrenamiento.id,
            'nombre': entrenamiento.nombre,
            'fecha': entrenamiento.fecha_hora.strftime('%d/%m/%Y'),
            'hora': entrenamiento.fecha_hora.strftime('%I:%M %p'),
            'equipo': entrenamiento.equipo.nombre,
            'cancha': cancha.nombre_escenario,
            'direccion': cancha.direccion_exacta,
            'localidad': cancha.localidad,
            'barrio': cancha.barrio,
            'lat': cancha.latitud,
            'lng': cancha.longitud,
        })

    return entrenamientos_mapa


def _construir_panel_asistencia(entrenamientos, equipo):
    if not equipo:
        return [], 0

    jugadores = list(Jugador.objects.filter(equipo=equipo).order_by('_dorsal', '_nombres'))
    if not jugadores:
        return [], 0

    try:
        asistencias = AsistenciaEntrenamiento.objects.filter(
            entrenamiento__in=entrenamientos,
            jugador__in=jugadores,
        )
    except (ProgrammingError, OperationalError):
        return [], len(jugadores)
    asistencia_map = {
        (asistencia.entrenamiento_id, asistencia.jugador_id): asistencia
        for asistencia in asistencias
    }

    panel = []
    for entrenamiento in entrenamientos:
        registros = []
        confirmados = 0
        sin_marcar = 0

        for jugador in jugadores:
            asistencia = asistencia_map.get((entrenamiento.id, jugador.id))
            estado = asistencia.asistio if asistencia else None

            if estado is not None:
                confirmados += 1
            else:
                sin_marcar += 1

            if estado is True:
                estado_label = 'Asistio'
                estado_badge = 'text-bg-success'
            elif estado is False:
                estado_label = 'Falto'
                estado_badge = 'text-bg-danger'
            else:
                estado_label = 'Sin marcar'
                estado_badge = 'text-bg-secondary'

            registros.append({
                'jugador': jugador,
                'estado': estado,
                'estado_label': estado_label,
                'estado_badge': estado_badge,
            })

        panel.append({
            'entrenamiento': entrenamiento,
            'registros': registros,
            'total_jugadores': len(jugadores),
            'confirmados': confirmados,
            'asistieron': sum(1 for item in registros if item['estado'] is True),
            'faltaron': sum(1 for item in registros if item['estado'] is False),
            'sin_marcar': sin_marcar,
        })

    return panel, len(jugadores)


def _asignar_estado_asistencia_jugador(entrenamientos, jugador):
    if not jugador or not entrenamientos:
        return

    try:
        asistencias = AsistenciaEntrenamiento.objects.filter(
            entrenamiento__in=entrenamientos,
            jugador=jugador,
        )
    except (ProgrammingError, OperationalError):
        asistencias = []

    asistencia_map = {
        asistencia.entrenamiento_id: asistencia
        for asistencia in asistencias
    }

    for entrenamiento in entrenamientos:
        asistencia = asistencia_map.get(entrenamiento.id)
        estado = asistencia.asistio if asistencia else None
        if estado is True:
            entrenamiento.estado_asistencia_label = 'Asistio'
            entrenamiento.estado_asistencia_badge = 'text-bg-success'
        elif estado is False:
            entrenamiento.estado_asistencia_label = 'Falto'
            entrenamiento.estado_asistencia_badge = 'text-bg-danger'
        else:
            entrenamiento.estado_asistencia_label = 'Sin marcar'
            entrenamiento.estado_asistencia_badge = 'text-bg-secondary'


@login_required
def lista_entrenamientos(request):
    user = request.user

    if user.rol == 'ADMIN':
        entrenamientos = Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').all()
    elif user.rol == 'ENTRENADOR':
        equipo = _obtener_equipo_entrenador(user)
        entrenamientos = Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').filter(
            equipo=equipo
        ) if equipo else Entrenamiento.objects.none()
    else:
        entrenamientos = Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').filter(
            equipo=user.jugador.equipo
        )

    panel_asistencia = []
    total_jugadores = 0
    if user.rol == 'ENTRENADOR':
        panel_asistencia, total_jugadores = _construir_panel_asistencia(
            entrenamientos,
            _obtener_equipo_entrenador(user)
        )

    return render(request, 'entrenamientos/lista.html', {
        'entrenamientos': entrenamientos,
        'panel_asistencia': panel_asistencia,
        'total_jugadores': total_jugadores,
    })


@login_required
def actualizar_asistencia_entrenamiento(request, pk):
    if request.method != 'POST':
        return redirect('lista_entrenamientos')

    if request.user.rol != 'ENTRENADOR':
        messages.error(request, 'No tienes permisos para registrar asistencia.')
        return redirect('lista_entrenamientos')

    entrenamiento = get_object_or_404(
        Entrenamiento.objects.select_related('equipo', 'entrenador'),
        pk=pk
    )

    if entrenamiento.entrenador != request.user.entrenador:
        messages.error(request, 'No puedes gestionar asistencia en un entrenamiento que no creaste.')
        return redirect('lista_entrenamientos')

    jugador = get_object_or_404(Jugador, pk=request.POST.get('jugador_id'), equipo=entrenamiento.equipo)
    estado = request.POST.get('estado')
    if estado not in ['asistio', 'falto']:
        messages.error(request, 'Estado de asistencia invalido.')
        return redirect('lista_entrenamientos')

    try:
        asistencia, _ = AsistenciaEntrenamiento.objects.get_or_create(
            entrenamiento=entrenamiento,
            jugador=jugador,
        )
    except (ProgrammingError, OperationalError):
        messages.error(request, 'La tabla de asistencia todavia no existe en la base de datos. Ejecuta las migraciones para habilitar esta funcion.')
        return redirect('lista_entrenamientos')
    asistencia.asistio = {
        'asistio': True,
        'falto': False,
    }[estado]
    asistencia.save()

    estado_label = {
        'asistio': 'asistio',
        'falto': 'falto',
    }[estado]
    messages.success(request, f'Asistencia actualizada: {jugador.nombres} {jugador.apellidos} {estado_label}.')
    return redirect('lista_entrenamientos')


@login_required
def crear_entrenamiento(request):
    if request.user.rol != 'ENTRENADOR':
        messages.error(request, 'No tienes permisos para crear entrenamientos.')
        return redirect('lista_entrenamientos')

    equipo = _obtener_equipo_entrenador(request.user)
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
        entrenamientos = list(entrenamientos)
        _asignar_estado_asistencia_jugador(entrenamientos, jugador)

    return render(request, 'entrenamientos/lista_jugador.html', {
        'entrenamientos': entrenamientos,
        'equipo': equipo,
        'jugador': jugador,
        'entrenamientos_mapa_json': json.dumps(_serializar_entrenamientos_mapa(entrenamientos)),
    })
