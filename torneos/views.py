from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from datetime import date

from .models import Torneo, InscripcionTorneo, Partido, EstadisticaJugador
from .forms import TorneoForm, PartidoForm, EstadisticaForm
from inscripciones.models import Equipo


# ─────────────────────────────────────────────
#  VISTAS ADMIN
# ─────────────────────────────────────────────

@login_required
def admin_lista_torneos(request):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    nombre = request.GET.get('nombre', '').strip()
    estado = request.GET.get('estado', '').strip()

    torneos = Torneo.objects.all()
    if nombre:
        torneos = torneos.filter(nombre__icontains=nombre)
    if estado:
        torneos = torneos.filter(estado=estado)

    return render(request, 'torneos/admin/lista_torneos.html', {
        'torneos': torneos,
        'request_nombre': nombre,
        'request_estado': estado,
        'estados': Torneo.Estado.choices,
    })


@login_required
def admin_crear_torneo(request):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    form = TorneoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Torneo creado exitosamente.')
        return redirect('torneos:admin_lista_torneos')

    return render(request, 'torneos/admin/crear_torneo.html', {'form': form})


@login_required
def admin_editar_torneo(request, torneo_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    torneo = get_object_or_404(Torneo, id=torneo_id)
    form = TorneoForm(request.POST or None, instance=torneo)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Torneo actualizado exitosamente.')
        return redirect('torneos:admin_lista_torneos')

    return render(request, 'torneos/admin/editar_torneo.html', {
        'form': form, 'torneo': torneo
    })


@login_required
def admin_eliminar_torneo(request, torneo_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    torneo = get_object_or_404(Torneo, id=torneo_id)
    if request.method == 'POST':
        torneo.delete()
        messages.success(request, 'Torneo eliminado.')
    return redirect('torneos:admin_lista_torneos')


@login_required
def admin_detalle_torneo(request, torneo_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    torneo   = get_object_or_404(Torneo, id=torneo_id)
    partidos = torneo.partidos.all().order_by('jornada', 'fecha')
    inscritos = torneo.inscripciones.filter(estado='ACTIVA').select_related('equipo')

    return render(request, 'torneos/admin/detalle_torneo.html', {
        'torneo': torneo,
        'partidos': partidos,
        'inscritos': inscritos,
    })


@login_required
def admin_crear_partido(request, torneo_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    torneo = get_object_or_404(Torneo, id=torneo_id)
    form   = PartidoForm(request.POST or None, torneo=torneo)

    if request.method == 'POST' and form.is_valid():
        partido = form.save(commit=False)
        partido.torneo = torneo
        partido.save()
        messages.success(request, 'Partido creado exitosamente.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    return render(request, 'torneos/admin/crear_partido.html', {
        'form': form, 'torneo': torneo
    })


@login_required
def admin_editar_partido(request, partido_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    partido = get_object_or_404(Partido, id=partido_id)
    form    = PartidoForm(request.POST or None, instance=partido, torneo=partido.torneo)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Partido actualizado.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=partido.torneo.id)

    return render(request, 'torneos/admin/crear_partido.html', {
        'form': form, 'torneo': partido.torneo, 'editando': True
    })


@login_required
def admin_desinscribir_equipo(request, inscripcion_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    inscripcion = get_object_or_404(InscripcionTorneo, id=inscripcion_id)
    torneo_id   = inscripcion.torneo.id
    if request.method == 'POST':
        inscripcion.estado = InscripcionTorneo.Estado.CANCELADA
        inscripcion.save()
        messages.success(request, 'Equipo desinscrito del torneo.')
    return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)


# ─────────────────────────────────────────────
#  VISTAS ENTRENADOR
# ─────────────────────────────────────────────

@login_required
def entrenador_lista_torneos(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    equipo = getattr(getattr(request.user, 'entrenador', None), 'equipo', None)

    torneos_disponibles = Torneo.objects.filter(
        estado=Torneo.Estado.PROXIMO,
        cupo_maximo__gt=0,
    )
    torneos_disponibles = [t for t in torneos_disponibles if t.puede_inscribirse]

    mis_inscripciones = []
    if equipo:
        mis_inscripciones = InscripcionTorneo.objects.filter(
            equipo=equipo, estado='ACTIVA'
        ).select_related('torneo')

    return render(request, 'torneos/entrenador/lista_torneos.html', {
        'torneos_disponibles': torneos_disponibles,
        'mis_inscripciones':   mis_inscripciones,
        'equipo': equipo,
    })


@login_required
def entrenador_inscribir(request, torneo_id):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    torneo = get_object_or_404(Torneo, id=torneo_id)
    equipo = getattr(getattr(request.user, 'entrenador', None), 'equipo', None)

    if not equipo:
        messages.error(request, 'No tienes un equipo registrado.')
        return redirect('torneos:entrenador_lista_torneos')

    if equipo.estado != 'APROBADO':
        messages.error(request, 'Tu equipo debe estar aprobado para inscribirse.')
        return redirect('torneos:entrenador_lista_torneos')

    if not torneo.puede_inscribirse:
        messages.error(request, 'Este torneo no está disponible para inscripciones.')
        return redirect('torneos:entrenador_lista_torneos')

    if InscripcionTorneo.objects.filter(torneo=torneo, equipo=equipo, estado='ACTIVA').exists():
        messages.error(request, 'Tu equipo ya está inscrito en este torneo.')
        return redirect('torneos:entrenador_lista_torneos')

    if request.method == 'POST':
        InscripcionTorneo.objects.create(torneo=torneo, equipo=equipo)
        messages.success(request, f'¡Tu equipo fue inscrito en {torneo.nombre}!')

    return redirect('torneos:entrenador_lista_torneos')


@login_required
def entrenador_cancelar_inscripcion(request, inscripcion_id):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    inscripcion = get_object_or_404(InscripcionTorneo, id=inscripcion_id)
    equipo = getattr(getattr(request.user, 'entrenador', None), 'equipo', None)

    if inscripcion.equipo != equipo:
        messages.error(request, 'No tienes permiso para esta acción.')
        return redirect('torneos:entrenador_lista_torneos')

    if inscripcion.torneo.estado != Torneo.Estado.PROXIMO:
        messages.error(request, 'No puedes cancelar un torneo que ya inició.')
        return redirect('torneos:entrenador_lista_torneos')

    if request.method == 'POST':
        inscripcion.estado = InscripcionTorneo.Estado.CANCELADA
        inscripcion.save()
        messages.success(request, 'Inscripción cancelada.')

    return redirect('torneos:entrenador_lista_torneos')


@login_required
def entrenador_mis_partidos(request, torneo_id):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    torneo = get_object_or_404(Torneo, id=torneo_id)
    equipo = getattr(getattr(request.user, 'entrenador', None), 'equipo', None)

    partidos = Partido.objects.filter(
        torneo=torneo
    ).filter(
        Q(equipo_local=equipo) | Q(equipo_visita=equipo)
    ).order_by('jornada', 'fecha')

    partidos_jugados   = partidos.filter(estado='FINALIZADO').count()
    partidos_restantes = partidos.exclude(estado='FINALIZADO').count()

    return render(request, 'torneos/entrenador/mis_partidos.html', {
        'torneo': torneo,
        'partidos': partidos,
        'equipo': equipo,
        'partidos_jugados': partidos_jugados,
        'partidos_restantes': partidos_restantes,
    })


# ─────────────────────────────────────────────
#  VISTAS JUGADOR
# ─────────────────────────────────────────────

@login_required
def jugador_mis_torneos(request):
    if request.user.rol != 'JUGADOR':
        return redirect('dashboard_admin')

    jugador = request.user

    # Buscar el equipo del jugador a través de la relación con el entrenador
    # El jugador pertenece a un equipo si existe un Equipo relacionado
    # Necesitamos buscar estadísticas del jugador en partidos
    estadisticas = EstadisticaJugador.objects.filter(
        jugador=jugador
    ).select_related('partido', 'partido__torneo', 'partido__equipo_local', 'partido__equipo_visita')

    # Torneos en los que participó (tuvo estadísticas)
    torneos_ids = estadisticas.values_list('partido__torneo_id', flat=True).distinct()
    torneos = Torneo.objects.filter(id__in=torneos_ids)

    # Totales globales del jugador
    totales = estadisticas.aggregate(
        total_goles=Sum('goles'),
        total_asistencias=Sum('asistencias'),
        total_amarillas=Sum('tarjetas_amarillas'),
        total_rojas=Sum('tarjetas_rojas'),
        total_minutos=Sum('minutos_jugados'),
    )

    # Estadísticas por torneo
    torneos_data = []
    for torneo in torneos:
        stats_torneo = estadisticas.filter(partido__torneo=torneo)
        partidos_jugados   = stats_torneo.count()
        partidos_restantes = Partido.objects.filter(
            torneo=torneo
        ).exclude(estado='FINALIZADO').count()

        torneos_data.append({
            'torneo': torneo,
            'goles':        stats_torneo.aggregate(s=Sum('goles'))['s'] or 0,
            'asistencias':  stats_torneo.aggregate(s=Sum('asistencias'))['s'] or 0,
            'amarillas':    stats_torneo.aggregate(s=Sum('tarjetas_amarillas'))['s'] or 0,
            'rojas':        stats_torneo.aggregate(s=Sum('tarjetas_rojas'))['s'] or 0,
            'minutos':      stats_torneo.aggregate(s=Sum('minutos_jugados'))['s'] or 0,
            'partidos_jugados':   partidos_jugados,
            'partidos_restantes': partidos_restantes,
        })

    return render(request, 'torneos/jugador/mis_torneos.html', {
        'torneos_data': torneos_data,
        'totales': totales,
    })