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
    equipos_ids = torneo.inscripciones.filter(
        estado='ACTIVA'
    ).values_list('equipo_id', flat=True)
    equipos = Equipo.objects.filter(id__in=equipos_ids)

    tabla = []
    for equipo in equipos:
        pl = Partido.objects.filter(
            torneo=torneo, equipo_local=equipo,
            estado='FINALIZADO', fase='GRUPOS'
        )
        pv = Partido.objects.filter(
            torneo=torneo, equipo_visita=equipo,
            estado='FINALIZADO', fase='GRUPOS'
        )
        pj = pl.count() + pv.count()
        gf = (sum(p.goles_local  for p in pl) +
              sum(p.goles_visita for p in pv))
        gc = (sum(p.goles_visita for p in pl) +
              sum(p.goles_local  for p in pv))
        pg = pe = pp = 0
        for p in pl:
            if   p.goles_local > p.goles_visita:  pg += 1
            elif p.goles_local < p.goles_visita:  pp += 1
            else:                                  pe += 1
        for p in pv:
            if   p.goles_visita > p.goles_local:  pg += 1
            elif p.goles_visita < p.goles_local:  pp += 1
            else:                                  pe += 1
        tabla.append({
            'equipo': equipo,
            'pj': pj, 'pg': pg, 'pe': pe, 'pp': pp,
            'gf': gf, 'gc': gc, 'dg': gf - gc,
            'pts': pg * 3 + pe,
        })
    tabla.sort(key=lambda x: (-x['pts'], -x['dg'], -x['gf']))
    return tabla


def _fixture_todos_contra_todos(equipos):
    """
    Algoritmo de rotación de círculo. Garantiza que cada par de equipos
    se enfrenta exactamente una vez. Devuelve lista de (local, visita, jornada).
    """
    equipos = list(equipos)
    n = len(equipos)
    if n < 2:
        return []
    if n % 2 != 0:
        equipos.append(None)
        n += 1

    mitad    = n // 2
    fijo     = equipos[0]
    rotantes = equipos[1:]
    partidos = []

    for jornada in range(1, n):
        for i in range(mitad):
            local  = fijo if i == 0 else rotantes[i - 1]
            visita = rotantes[n - 2 - i]
            if local is not None and visita is not None:
                if jornada % 2 == 0:
                    local, visita = visita, local
                partidos.append((local, visita, jornada))
        rotantes = [rotantes[-1]] + rotantes[:-1]

    return partidos


def _clasificados_para_siguiente(torneo, n):
    """Retorna los primeros n equipos de la tabla de grupos."""
    tabla = _calcular_tabla(torneo)
    return [fila['equipo'] for fila in tabla[:n]]


def _grupos_completos(torneo):
    """True si todos los partidos de grupos están finalizados o suspendidos."""
    grupos = torneo.partidos.filter(fase='GRUPOS')
    if not grupos.exists():
        return False
    return not grupos.exclude(
        estado__in=['FINALIZADO', 'SUSPENDIDO']
    ).exists()


def _fase_completa(torneo, fase):
    partidos = torneo.partidos.filter(fase=fase)
    if not partidos.exists():
        return False
    return not partidos.exclude(
        estado__in=['FINALIZADO', 'SUSPENDIDO']
    ).exists()


# ─────────────────────────────────────────────
#  ADMIN — TORNEOS
# ─────────────────────────────────────────────

@login_required
def admin_lista_torneos(request):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    for t in Torneo.objects.exclude(estado__in=['CANCELADO', 'FINALIZADO']):
        t.actualizar_estado()

    nombre = request.GET.get('nombre', '').strip()
    estado = request.GET.get('estado', '').strip()
    torneos = Torneo.objects.all()
    if nombre:
        torneos = torneos.filter(nombre__icontains=nombre)
    if estado:
        torneos = torneos.filter(estado=estado)

    return render(request, 'torneos/admin/lista_torneos.html', {
        'torneos':         torneos,
        'request_nombre':  nombre,
        'request_estado':  estado,
        'estados':         Torneo.Estado.choices,
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

    torneo = get_object_or_404(Torneo, id=torneo_id)
    torneo.actualizar_estado()

    partidos_grupos    = torneo.partidos.filter(fase='GRUPOS').order_by('jornada', 'fecha')
    partidos_cuartos   = torneo.partidos.filter(fase='CUARTOS').order_by('fecha')
    partidos_semi      = torneo.partidos.filter(fase='SEMIFINAL').order_by('fecha')
    partidos_tercero   = torneo.partidos.filter(fase='TERCER_PUES').order_by('fecha')
    partidos_final     = torneo.partidos.filter(fase='FINAL').order_by('fecha')
    inscritos          = torneo.inscripciones.filter(estado='ACTIVA').select_related('equipo')
    tabla              = _calcular_tabla(torneo)

    # Qué botones mostrar
    puede_fixture_grupos   = (
        not torneo.partidos.filter(fase='GRUPOS').exists()
        and inscritos.count() >= 2
    )
    puede_avanzar_cuartos  = (
        torneo.formato == 'GRUPOS_CUARTOS'
        and _grupos_completos(torneo)
        and not torneo.partidos.filter(fase='CUARTOS').exists()
        and len(tabla) >= 8
    )
    puede_avanzar_semi     = (
        torneo.formato in ['GRUPOS_SEMI', 'GRUPOS_CUARTOS']
        and not torneo.partidos.filter(fase='SEMIFINAL').exists()
        and (
            (_fase_completa(torneo, 'CUARTOS') and torneo.partidos.filter(fase='CUARTOS').exists())
            or
            (_grupos_completos(torneo) and torneo.formato == 'GRUPOS_SEMI' and not torneo.partidos.filter(fase='CUARTOS').exists() and len(tabla) >= 4)
        )
    )
    puede_avanzar_final    = (
        torneo.formato in ['GRUPOS_FINAL', 'GRUPOS_SEMI', 'GRUPOS_CUARTOS']
        and not torneo.partidos.filter(fase='FINAL').exists()
        and (
            (_fase_completa(torneo, 'SEMIFINAL') and torneo.partidos.filter(fase='SEMIFINAL').exists())
            or
            (_grupos_completos(torneo) and torneo.formato == 'GRUPOS_FINAL' and len(tabla) >= 2)
        )
    )

    partidos_finalizados = torneo.partidos.filter(estado='FINALIZADO').count()

    return render(request, 'torneos/admin/detalle_torneo.html', {
        'torneo':                torneo,
        'inscritos':             inscritos,
        'tabla':                 tabla,
        'partidos_grupos':       partidos_grupos,
        'partidos_cuartos':      partidos_cuartos,
        'partidos_semi':         partidos_semi,
        'partidos_tercero':      partidos_tercero,
        'partidos_final':        partidos_final,
        'puede_fixture_grupos':  puede_fixture_grupos,
        'puede_avanzar_cuartos': puede_avanzar_cuartos,
        'puede_avanzar_semi':    puede_avanzar_semi,
        'puede_avanzar_final':   puede_avanzar_final,
        'partidos_finalizados':  partidos_finalizados,
    })


# ─────────────────────────────────────────────
#  ADMIN — PARTIDOS
# ─────────────────────────────────────────────

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
        messages.success(request, 'Partido creado.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    return render(request, 'torneos/admin/crear_partido.html', {
        'form': form, 'torneo': torneo
    })


@login_required
def admin_editar_partido(request, partido_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    partido = get_object_or_404(Partido, id=partido_id)
    form    = PartidoForm(
        request.POST or None,
        instance=partido,
        torneo=partido.torneo
    )

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
        messages.success(request, 'Equipo desinscrito.')
    return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)


# ─────────────────────────────────────────────
#  ADMIN — GENERACIÓN DE FASES
# ─────────────────────────────────────────────

@login_required
def admin_generar_fixture(request, torneo_id):
    """Genera la fase de grupos (todos contra todos)."""
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    torneo = get_object_or_404(Torneo, id=torneo_id)

    if request.method != 'POST':
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    if torneo.partidos.filter(fase='GRUPOS').exists():
        messages.error(request, 'Ya existe una fase de grupos para este torneo.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    equipos = list(
        Equipo.objects.filter(
            id__in=torneo.inscripciones.filter(
                estado='ACTIVA'
            ).values_list('equipo_id', flat=True)
        )
    )

    if len(equipos) < 2:
        messages.error(request, 'Se necesitan al menos 2 equipos inscritos.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    pares_vistos = set()
    partidos_a_crear = _fixture_todos_contra_todos(equipos)

    creados = 0
    for local, visita, jornada in partidos_a_crear:
        par = tuple(sorted([local.id, visita.id]))
        if par in pares_vistos:
            continue
        pares_vistos.add(par)
        Partido.objects.create(
            torneo=torneo,
            equipo_local=local,
            equipo_visita=visita,
            fase=Partido.Fase.GRUPOS,
            jornada=jornada,
            fecha=torneo.fecha_inicio,
            estado=Partido.Estado.PROGRAMADO,
        )
        creados += 1

    torneo.fase_actual = 'GRUPOS'
    torneo.save(update_fields=['fase_actual'])

    n_jornadas = max(j for _, _, j in partidos_a_crear) if partidos_a_crear else 0
    messages.success(
        request,
        f'Fase de grupos generada: {creados} partido(s) en {n_jornadas} jornada(s). '
        f'Asigna las fechas exactas editando cada partido.'
    )
    return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)


@login_required
def admin_generar_cuartos(request, torneo_id):
    """Genera cuartos de final con los 8 primeros de la tabla."""
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    torneo = get_object_or_404(Torneo, id=torneo_id)

    if request.method != 'POST':
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    if not _grupos_completos(torneo):
        messages.error(request, 'Todos los partidos de grupos deben estar finalizados.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    if torneo.partidos.filter(fase='CUARTOS').exists():
        messages.error(request, 'Los cuartos de final ya fueron generados.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    clasificados = _clasificados_para_siguiente(torneo, 8)
    if len(clasificados) < 8:
        messages.error(request, f'Se necesitan 8 equipos clasificados. Solo hay {len(clasificados)}.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    # 1° vs 8°, 2° vs 7°, 3° vs 6°, 4° vs 5°
    enfrentamientos = [
        (clasificados[0], clasificados[7]),
        (clasificados[1], clasificados[6]),
        (clasificados[2], clasificados[5]),
        (clasificados[3], clasificados[4]),
    ]
    for local, visita in enfrentamientos:
        Partido.objects.create(
            torneo=torneo,
            equipo_local=local,
            equipo_visita=visita,
            fase=Partido.Fase.CUARTOS,
            jornada=1,
            fecha=torneo.fecha_inicio,
            estado=Partido.Estado.PROGRAMADO,
        )

    torneo.fase_actual = 'CUARTOS'
    torneo.save(update_fields=['fase_actual'])

    messages.success(request, 'Cuartos de final generados (4 partidos). Asigna fechas y registra resultados.')
    return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)


@login_required
def admin_generar_semifinales(request, torneo_id):
    """Genera semifinales. Toma los 4 primeros o los ganadores de cuartos."""
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    torneo = get_object_or_404(Torneo, id=torneo_id)

    if request.method != 'POST':
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    if torneo.partidos.filter(fase='SEMIFINAL').exists():
        messages.error(request, 'Las semifinales ya fueron generadas.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    # Determinar los 4 semifinalistas
    cuartos = torneo.partidos.filter(fase='CUARTOS', estado='FINALIZADO')
    if cuartos.exists():
        if not _fase_completa(torneo, 'CUARTOS'):
            messages.error(request, 'Todos los cuartos de final deben estar finalizados.')
            return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)
        # Ganadores de cuartos en orden
        semifinalistas = []
        for p in torneo.partidos.filter(fase='CUARTOS').order_by('id'):
            if p.goles_local > p.goles_visita:
                semifinalistas.append(p.equipo_local)
            elif p.goles_visita > p.goles_local:
                semifinalistas.append(p.equipo_visita)
            else:
                messages.error(request, f'El partido {p} terminó empatado. Define un ganador antes de avanzar.')
                return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)
    else:
        if not _grupos_completos(torneo):
            messages.error(request, 'Todos los partidos de grupos deben estar finalizados.')
            return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)
        semifinalistas = _clasificados_para_siguiente(torneo, 4)
        if len(semifinalistas) < 4:
            messages.error(request, f'Se necesitan 4 equipos. Solo hay {len(semifinalistas)}.')
            return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    # Semi 1: [0] vs [3], Semi 2: [1] vs [2]
    Partido.objects.create(
        torneo=torneo, equipo_local=semifinalistas[0], equipo_visita=semifinalistas[3],
        fase=Partido.Fase.SEMIFINAL, jornada=1, fecha=torneo.fecha_inicio,
        estado=Partido.Estado.PROGRAMADO,
    )
    Partido.objects.create(
        torneo=torneo, equipo_local=semifinalistas[1], equipo_visita=semifinalistas[2],
        fase=Partido.Fase.SEMIFINAL, jornada=1, fecha=torneo.fecha_inicio,
        estado=Partido.Estado.PROGRAMADO,
    )

    torneo.fase_actual = 'SEMIFINAL'
    torneo.save(update_fields=['fase_actual'])

    messages.success(request, 'Semifinales generadas (2 partidos). Registra los resultados para avanzar a la final.')
    return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)


@login_required
def admin_generar_final(request, torneo_id):
    """Genera la final y el partido por el tercer puesto."""
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    torneo = get_object_or_404(Torneo, id=torneo_id)

    if request.method != 'POST':
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    if torneo.partidos.filter(fase='FINAL').exists():
        messages.error(request, 'La final ya fue generada.')
        return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

    semis = torneo.partidos.filter(fase='SEMIFINAL')

    if semis.exists():
        if not _fase_completa(torneo, 'SEMIFINAL'):
            messages.error(request, 'Ambas semifinales deben estar finalizadas.')
            return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

        finalistas   = []
        perdedores   = []
        for p in semis.order_by('id'):
            if p.goles_local > p.goles_visita:
                finalistas.append(p.equipo_local)
                perdedores.append(p.equipo_visita)
            elif p.goles_visita > p.goles_local:
                finalistas.append(p.equipo_visita)
                perdedores.append(p.equipo_local)
            else:
                messages.error(request, f'La semifinal {p} terminó empatada. Define un ganador.')
                return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

        if len(finalistas) < 2:
            messages.error(request, 'No se pudieron determinar los finalistas.')
            return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)

        # Tercer puesto
        Partido.objects.create(
            torneo=torneo, equipo_local=perdedores[0], equipo_visita=perdedores[1],
            fase=Partido.Fase.TERCER_PUES, jornada=1, fecha=torneo.fecha_fin,
            estado=Partido.Estado.PROGRAMADO,
        )

    else:
        # Formato GRUPOS_FINAL: los 2 primeros van directo a la final
        if not _grupos_completos(torneo):
            messages.error(request, 'Todos los partidos de grupos deben estar finalizados.')
            return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)
        clasificados = _clasificados_para_siguiente(torneo, 2)
        if len(clasificados) < 2:
            messages.error(request, 'Se necesitan al menos 2 equipos clasificados.')
            return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)
        finalistas = clasificados

    Partido.objects.create(
        torneo=torneo, equipo_local=finalistas[0], equipo_visita=finalistas[1],
        fase=Partido.Fase.FINAL, jornada=1, fecha=torneo.fecha_fin,
        estado=Partido.Estado.PROGRAMADO,
    )

    torneo.fase_actual = 'FINAL'
    torneo.save(update_fields=['fase_actual'])

    messages.success(request, 'Final generada. ¡Registra el resultado para coronar al campeón!')
    return redirect('torneos:admin_detalle_torneo', torneo_id=torneo_id)


# ─────────────────────────────────────────────
#  ENTRENADOR
# ─────────────────────────────────────────────

@login_required
def entrenador_lista_torneos(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    equipo = getattr(getattr(request.user, 'entrenador', None), 'equipo', None)

    mis_inscripciones = []
    ids_inscritos     = []
    if equipo:
        mis_inscripciones = InscripcionTorneo.objects.filter(
            equipo=equipo, estado='ACTIVA'
        ).select_related('torneo')
        ids_inscritos = list(mis_inscripciones.values_list('torneo_id', flat=True))

    torneos_qs = Torneo.objects.filter(
        estado=Torneo.Estado.PROXIMO,
        cupo_maximo__gt=0,
    ).exclude(id__in=ids_inscritos)

    if equipo:
        torneos_qs = torneos_qs.filter(categoria=equipo.categoria)

    torneos_disponibles = [t for t in torneos_qs if t.puede_inscribirse]

    return render(request, 'torneos/entrenador/lista_torneos.html', {
        'torneos_disponibles': torneos_disponibles,
        'mis_inscripciones':   mis_inscripciones,
        'equipo':              equipo,
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

    if equipo.categoria != torneo.categoria:
        messages.error(
            request,
            f'Tu equipo es categoría {equipo.categoria_display} y este '
            f'torneo es para {torneo.get_categoria_display()}.'
        )
        return redirect('torneos:entrenador_lista_torneos')

    if not torneo.puede_inscribirse:
        messages.error(request, 'Este torneo no acepta inscripciones.')
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
    if request.user.rol != 'ADMIN' and request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    inscripcion = get_object_or_404(InscripcionTorneo, id=inscripcion_id)
    equipo      = getattr(getattr(request.user, 'entrenador', None), 'equipo', None)

    if request.user.rol == 'ENTRENADOR' and inscripcion.equipo != equipo:
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
    ).order_by('fase', 'jornada', 'fecha')

    pj = partidos.filter(estado='FINALIZADO').count()
    pr = partidos.exclude(estado__in=['FINALIZADO', 'SUSPENDIDO']).count()

    return render(request, 'torneos/entrenador/mis_partidos.html', {
        'torneo':             torneo,
        'partidos':           partidos,
        'equipo':             equipo,
        'partidos_jugados':   pj,
        'partidos_restantes': pr,
        'tabla':              _calcular_tabla(torneo),
    })


# ─────────────────────────────────────────────
#  JUGADOR
# ─────────────────────────────────────────────

@login_required
def jugador_mis_torneos(request):
    if request.user.rol != 'JUGADOR':
        return redirect('dashboard_admin')

    jugador_obj = getattr(request.user, 'jugador', None)
    equipo      = jugador_obj.equipo if jugador_obj else None

    torneos_data = []
    if equipo:
        for insc in InscripcionTorneo.objects.filter(
            equipo=equipo
        ).select_related('torneo').order_by('-torneo__fecha_inicio'):
            torneo = insc.torneo
            torneo.actualizar_estado()

            partidos_equipo = Partido.objects.filter(
                torneo=torneo
            ).filter(Q(equipo_local=equipo) | Q(equipo_visita=equipo))

            stats = EstadisticaJugador.objects.filter(
                jugador=jugador_obj, partido__torneo=torneo,
            ).aggregate(
                total_goles=Sum('goles'),
                total_asistencias=Sum('asistencias'),
                total_amarillas=Sum('tarjetas_amarillas'),
                total_rojas=Sum('tarjetas_rojas'),
                total_minutos=Sum('minutos_jugados'),
            )

            torneos_data.append({
                'torneo':             torneo,
                'partidos_jugados':   partidos_equipo.filter(estado='FINALIZADO').count(),
                'partidos_restantes': partidos_equipo.exclude(estado__in=['FINALIZADO','SUSPENDIDO']).count(),
                'goles':       stats['total_goles']       or 0,
                'asistencias': stats['total_asistencias'] or 0,
                'amarillas':   stats['total_amarillas']   or 0,
                'rojas':       stats['total_rojas']       or 0,
                'minutos':     stats['total_minutos']     or 0,
            })

    totales = {'total_goles': 0, 'total_asistencias': 0, 'total_rojas': 0, 'total_minutos': 0}
    if jugador_obj:
        agg = EstadisticaJugador.objects.filter(jugador=jugador_obj).aggregate(
            total_goles=Sum('goles'), total_asistencias=Sum('asistencias'),
            total_rojas=Sum('tarjetas_rojas'), total_minutos=Sum('minutos_jugados'),
        )
        totales = {k: v or 0 for k, v in agg.items()}

    return render(request, 'torneos/jugador/mis_torneos.html', {
        'torneos_data': torneos_data,
        'totales':      totales,
        'equipo':       equipo,
    })