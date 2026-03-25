from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from datetime import date

from .models import Torneo, InscripcionTorneo, Partido, EstadisticaJugador
from .forms import TorneoForm, PartidoForm, EstadisticaForm
from inscripciones.models import Equipo


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _calcular_tabla(torneo):
    """
    Devuelve una lista de dicts con la tabla de posiciones del torneo,
    ordenada por puntos, diferencia de gol, goles a favor.
    """
    equipos_ids = torneo.inscripciones.filter(
        estado='ACTIVA'
    ).values_list('equipo_id', flat=True)
    equipos = Equipo.objects.filter(id__in=equipos_ids)

    tabla = []
    for equipo in equipos:
        partidos_local  = Partido.objects.filter(torneo=torneo, equipo_local=equipo,  estado='FINALIZADO')
        partidos_visita = Partido.objects.filter(torneo=torneo, equipo_visita=equipo, estado='FINALIZADO')

        pj = partidos_local.count() + partidos_visita.count()
        gf = (sum(p.goles_local  for p in partidos_local) +
              sum(p.goles_visita for p in partidos_visita))
        gc = (sum(p.goles_visita for p in partidos_local) +
              sum(p.goles_local  for p in partidos_visita))

        pg = pk = pe = 0
        for p in partidos_local:
            if p.goles_local > p.goles_visita:   pg += 1
            elif p.goles_local < p.goles_visita: pk += 1
            else:                                 pe += 1
        for p in partidos_visita:
            if p.goles_visita > p.goles_local:   pg += 1
            elif p.goles_visita < p.goles_local: pk += 1
            else:                                 pe += 1

        puntos = pg * 3 + pe
        tabla.append({
            'equipo': equipo,
            'pj': pj, 'pg': pg, 'pe': pe, 'pp': pk,
            'gf': gf, 'gc': gc, 'dg': gf - gc,
            'pts': puntos,
        })

    tabla.sort(key=lambda x: (-x['pts'], -x['dg'], -x['gf']))
    return tabla


def _generar_fixture_todos_contra_todos(torneo):
    """
    Genera fixture de todos contra todos (ida).
    Retorna lista de (equipo_local, equipo_visita, jornada).
    Usa algoritmo de rotación de círculo.
    """
    equipos = list(
        Equipo.objects.filter(
            id__in=torneo.inscripciones.filter(
                estado='ACTIVA'
            ).values_list('equipo_id', flat=True)
        )
    )
    n = len(equipos)
    if n < 2:
        return []

    # Si n es impar, agregar un "equipo libre" (None = descanso)
    if n % 2 != 0:
        equipos.append(None)
        n += 1

    partidos = []
    mitad = n // 2
    fijo = equipos[0]
    rotantes = equipos[1:]

    for jornada in range(1, n):
        for i in range(mitad):
            local  = fijo if i == 0 else rotantes[i - 1]
            visita = rotantes[n - 2 - i]
            # Saltar si alguno es el equipo "libre"
            if local is not None and visita is not None:
                # Alternar local/visita en jornadas pares
                if jornada % 2 == 0:
                    local, visita = visita, local
                partidos.append((local, visita, jornada))
        # Rotar: mover el último de rotantes al frente
        rotantes = [rotantes[-1]] + rotantes[:-1]

    return partidos


# ─────────────────────────────────────────────
#  VISTAS ADMIN
# ─────────────────────────────────────────────

@login_required
def admin_lista_torneos(request):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    # Actualizar estados automáticamente al listar
    for torneo in Torneo.objects.exclude(estado__in=['CANCELADO', 'FINALIZADO']):
        torneo.actualizar_estado()

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
    form   = TorneoForm(request.POST or None, instance=torneo)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Torneo actualizado exitosamente.')
        return redirect('torneos:admin_lista_torneos')

    return render(request, 'torneos/admin/editar_torneo.html', {
        'form': form, 'torneo': torneo, 'editando': True
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
    torneo.actualizar_estado()
    partidos  = torneo.partidos.all().order_by('jornada', 'fecha')
    inscritos = torneo.inscripciones.filter(estado='ACTIVA').select_related('equipo')
    tabla     = _calcular_tabla(torneo)

    return render(request, 'torneos/admin/detalle_torneo.html', {
        'torneo':   torneo,
        'partidos': partidos,
        'inscritos': inscritos,
        'tabla':    tabla,
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


@login_required
def admin_generar_fixture(request, torneo_id):
    """Genera automáticamente el fixture todos contra todos."""
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    torneo = get_object_or_404(Torneo, id=torneo_id)

    if request.method == 'POST':
        # Verificar que haya al menos 2 equipos
        equipos_count = torneo.inscripciones.filter(estado='ACTIVA').count()
        if equipos_count < 2:
            messages.error(request, 'Se necesitan al menos 2 equipos inscritos para generar el fixture.')
            return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

        # Verificar que no existan partidos ya
        if torneo.partidos.exists():
            messages.error(request, 'Ya existen partidos en este torneo. Elimínalos antes de generar el fixture.')
            return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

        partidos = _generar_fixture_todos_contra_todos(torneo)
        for local, visita, jornada in partidos:
            Partido.objects.create(
                torneo=torneo,
                equipo_local=local,
                equipo_visita=visita,
                jornada=jornada,
                fecha=torneo.fecha_inicio,  # Fecha provisional — el admin edita después
                estado=Partido.Estado.PROGRAMADO,
            )

        messages.success(
            request,
            f'Fixture generado: {len(partidos)} partido(s) en {max(j for _, _, j in partidos)} jornada(s). '
            f'Recuerda asignar las fechas exactas a cada partido.'
        )

    return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)


# ─────────────────────────────────────────────
#  VISTAS ENTRENADOR
# ─────────────────────────────────────────────

@login_required
def entrenador_lista_torneos(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    equipo = getattr(getattr(request.user, 'entrenador', None), 'equipo', None)

    mis_inscripciones = []
    ids_inscritos = []
    if equipo:
        mis_inscripciones = InscripcionTorneo.objects.filter(
            equipo=equipo, estado='ACTIVA'
        ).select_related('torneo')
        ids_inscritos = list(mis_inscripciones.values_list('torneo_id', flat=True))

    # Solo torneos de la misma categoría del equipo, excluyendo los ya inscritos
    torneos_disponibles_qs = Torneo.objects.filter(
        estado=Torneo.Estado.PROXIMO,
        cupo_maximo__gt=0,
    ).exclude(id__in=ids_inscritos)

    if equipo:
        torneos_disponibles_qs = torneos_disponibles_qs.filter(categoria=equipo.categoria)

    torneos_disponibles = [t for t in torneos_disponibles_qs if t.puede_inscribirse]

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

    # Validar categoría
    if equipo.categoria != torneo.categoria:
        messages.error(
            request,
            f'Tu equipo es categoría {equipo.get__categoria_display()} y este torneo '
            f'es para categoría {torneo.get_categoria_display()}. No puedes inscribirte.'
        )
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
    tabla              = _calcular_tabla(torneo)

    return render(request, 'torneos/entrenador/mis_partidos.html', {
        'torneo':              torneo,
        'partidos':            partidos,
        'equipo':              equipo,
        'partidos_jugados':    partidos_jugados,
        'partidos_restantes':  partidos_restantes,
        'tabla':               tabla,
    })


# ─────────────────────────────────────────────
#  VISTAS JUGADOR
# ─────────────────────────────────────────────

@login_required
def jugador_mis_torneos(request):
    if request.user.rol != 'JUGADOR':
        return redirect('dashboard_admin')

    from accounts.models import Jugador as JugadorModel
    jugador_obj = getattr(request.user, 'jugador', None)
    equipo      = jugador_obj.equipo if jugador_obj else None

    # Torneos en los que participó el equipo del jugador
    torneos_data = []
    if equipo:
        inscripciones = InscripcionTorneo.objects.filter(
            equipo=equipo
        ).select_related('torneo').order_by('-torneo__fecha_inicio')

        for insc in inscripciones:
            torneo = insc.torneo
            torneo.actualizar_estado()

            # Todos los partidos del equipo en ese torneo
            partidos_equipo = Partido.objects.filter(
                torneo=torneo
            ).filter(
                Q(equipo_local=equipo) | Q(equipo_visita=equipo)
            )
            pj = partidos_equipo.filter(estado='FINALIZADO').count()
            pr = partidos_equipo.exclude(estado='FINALIZADO').exclude(estado='SUSPENDIDO').count()

            # Estadísticas del jugador en ese torneo
            stats = EstadisticaJugador.objects.filter(
                jugador=jugador_obj,
                partido__torneo=torneo,
            ).aggregate(
                total_goles=Sum('goles'),
                total_asistencias=Sum('asistencias'),
                total_amarillas=Sum('tarjetas_amarillas'),
                total_rojas=Sum('tarjetas_rojas'),
                total_minutos=Sum('minutos_jugados'),
            )

            torneos_data.append({
                'torneo':              torneo,
                'inscripcion':         insc,
                'partidos_jugados':    pj,
                'partidos_restantes':  pr,
                'goles':        stats['total_goles']       or 0,
                'asistencias':  stats['total_asistencias'] or 0,
                'amarillas':    stats['total_amarillas']   or 0,
                'rojas':        stats['total_rojas']       or 0,
                'minutos':      stats['total_minutos']     or 0,
            })

    # Totales globales
    totales = {'total_goles': 0, 'total_asistencias': 0,
               'total_rojas': 0, 'total_minutos': 0}
    if jugador_obj:
        agg = EstadisticaJugador.objects.filter(jugador=jugador_obj).aggregate(
            total_goles=Sum('goles'),
            total_asistencias=Sum('asistencias'),
            total_rojas=Sum('tarjetas_rojas'),
            total_minutos=Sum('minutos_jugados'),
        )
        totales = {k: v or 0 for k, v in agg.items()}

    return render(request, 'torneos/jugador/mis_torneos.html', {
        'torneos_data': torneos_data,
        'totales':      totales,
        'equipo':       equipo,
    })