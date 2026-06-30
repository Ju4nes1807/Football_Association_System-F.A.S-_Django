import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_datetime
from django.utils.html import escape

from accounts.models import Jugador
from .forms import EntrenamientoForm, obtener_canchas_disponibles
from .models import AsistenciaEntrenamiento, Entrenamiento
from inscripciones.seleccion_equipo import equipo_activo, equipos_del_entrenador


def _enviar_correo_entrenamiento(entrenamiento, creado=True):
    jugadores = Jugador.objects.filter(
        equipo=entrenamiento.equipo,
        is_active=True,
    ).exclude(_email='')
    destinatarios = list(jugadores.values_list('_email', flat=True))
    if not destinatarios:
        return 0

    asunto = 'Entrenamiento programado en F.A.S' if creado else 'Entrenamiento actualizado en F.A.S'
    fecha = entrenamiento.fecha_hora.strftime('%d/%m/%Y %H:%M')
    lugar = entrenamiento.lugar_detallado
    texto = (
        f'Hola,\n\n'
        f'Tienes una sesion de entrenamiento con {entrenamiento.equipo.nombre}.\n\n'
        f'Sesion: {entrenamiento.nombre}\n'
        f'Fecha: {fecha}\n'
        f'Lugar: {lugar}\n\n'
        f'Revisa F.A.S para mas detalles.\n'
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;background:#f4f7fb;padding:24px;color:#172033;">
      <div style="max-width:640px;margin:auto;background:#fff;border-radius:18px;overflow:hidden;border:1px solid #e5e7eb;">
        <div style="background:#0d47a1;color:#fff;padding:20px 24px;border-bottom:4px solid #ffb300;">
          <p style="margin:0 0 6px;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#fff4cc;">Football Association System</p>
          <h2 style="margin:0;font-size:24px;">{escape(asunto)}</h2>
        </div>
        <div style="padding:24px;">
          <p>Tienes una sesion de entrenamiento con <strong>{escape(entrenamiento.equipo.nombre)}</strong>.</p>
          <div style="background:#edf5ff;border-left:5px solid #ffb300;border-radius:12px;padding:16px;">
            <p><strong>Sesion:</strong> {escape(entrenamiento.nombre)}</p>
            <p><strong>Fecha:</strong> {escape(fecha)}</p>
            <p><strong>Lugar:</strong> {escape(lugar)}</p>
          </div>
          <p style="color:#667085;">Llega con tiempo, prepara tus implementos y revisa cualquier cambio en F.A.S.</p>
        </div>
      </div>
    </div>
    """
    msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, destinatarios)
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=True)
    return len(destinatarios)


def _obtener_equipo_entrenador(request):
    return equipo_activo(request)


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
        equipo = _obtener_equipo_entrenador(request)
        entrenamientos = Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').filter(
            equipo=equipo
        ) if equipo else Entrenamiento.objects.none()
    else:
        entrenamientos = Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').filter(
            equipo=user.jugador.equipo
        )

    entrenamientos = list(entrenamientos)
    for entrenamiento in entrenamientos:
        entrenamiento.actualizar_estado(guardar=True)

    panel_asistencia = []
    total_jugadores = 0
    if user.rol == 'ENTRENADOR':
        panel_asistencia, total_jugadores = _construir_panel_asistencia(
            entrenamientos,
            _obtener_equipo_entrenador(request)
        )

    return render(request, 'entrenamientos/lista.html', {
        'entrenamientos': entrenamientos,
        'panel_asistencia': panel_asistencia,
        'total_jugadores': total_jugadores,
        'equipo': _obtener_equipo_entrenador(request) if user.rol == 'ENTRENADOR' else None,
        'equipos': equipos_del_entrenador(user) if user.rol == 'ENTRENADOR' else [],
    })


@login_required
def actualizar_asistencia_entrenamiento(request, pk):
    es_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method != 'POST':
        return redirect('lista_entrenamientos')

    if request.user.rol != 'ENTRENADOR':
        if es_ajax:
            return JsonResponse({'ok': False, 'error': 'No tienes permisos para registrar asistencia.'}, status=403)
        messages.error(request, 'No tienes permisos para registrar asistencia.')
        return redirect('lista_entrenamientos')

    entrenamiento = get_object_or_404(
        Entrenamiento.objects.select_related('equipo', 'entrenador'),
        pk=pk
    )

    if entrenamiento.entrenador != request.user.entrenador:
        if es_ajax:
            return JsonResponse({'ok': False, 'error': 'No puedes gestionar este entrenamiento.'}, status=403)
        messages.error(request, 'No puedes gestionar asistencia en un entrenamiento que no creaste.')
        return redirect('lista_entrenamientos')

    jugador = get_object_or_404(Jugador, pk=request.POST.get('jugador_id'), equipo=entrenamiento.equipo)
    estado = request.POST.get('estado')
    estados_asistencia = {
        'asistio': {
            'valor': True,
            'label': 'Asistio',
            'mensaje': 'asistio',
            'badge': 'text-bg-success',
        },
        'falto': {
            'valor': False,
            'label': 'Falto',
            'mensaje': 'falto',
            'badge': 'text-bg-danger',
        },
        'sin_marcar': {
            'valor': None,
            'label': 'Sin marcar',
            'mensaje': 'sin marcar',
            'badge': 'text-bg-secondary',
        },
    }
    if estado not in estados_asistencia:
        if es_ajax:
            return JsonResponse({'ok': False, 'error': 'Estado de asistencia invalido.'}, status=400)
        messages.error(request, 'Estado de asistencia invalido.')
        return redirect('lista_entrenamientos')

    try:
        asistencia, _ = AsistenciaEntrenamiento.objects.get_or_create(
            entrenamiento=entrenamiento,
            jugador=jugador,
        )
    except (ProgrammingError, OperationalError):
        if es_ajax:
            return JsonResponse({'ok': False, 'error': 'La tabla de asistencia todavia no existe.'}, status=500)
        messages.error(request, 'La tabla de asistencia todavia no existe en la base de datos. Ejecuta las migraciones para habilitar esta funcion.')
        return redirect('lista_entrenamientos')
    estado_config = estados_asistencia[estado]
    asistencia.asistio = estado_config['valor']
    asistencia.save()

    if es_ajax:
        asistencias = AsistenciaEntrenamiento.objects.filter(entrenamiento=entrenamiento)
        asistieron = asistencias.filter(asistio=True).count()
        faltaron = asistencias.filter(asistio=False).count()
        total_jugadores = Jugador.objects.filter(equipo=entrenamiento.equipo).count()
        sin_marcar = max(0, total_jugadores - asistencias.exclude(asistio__isnull=True).count())
        return JsonResponse({
            'ok': True,
            'jugador_id': jugador.id,
            'estado': estado,
            'estado_label': estado_config['label'],
            'estado_badge': estado_config['badge'],
            'asistieron': asistieron,
            'faltaron': faltaron,
            'sin_marcar': sin_marcar,
            'message': f"{jugador.nombres} {jugador.apellidos}: {estado_config['mensaje']}.",
        })

    messages.success(request, f"Asistencia actualizada: {jugador.nombres} {jugador.apellidos} {estado_config['mensaje']}.")
    return redirect('lista_entrenamientos')


@login_required
def crear_entrenamiento(request):
    if request.user.rol != 'ENTRENADOR':
        messages.error(request, 'No tienes permisos para crear entrenamientos.')
        return redirect('lista_entrenamientos')

    equipo = _obtener_equipo_entrenador(request)
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
            enviados = _enviar_correo_entrenamiento(entrenamiento, creado=True)
            if enviados:
                messages.success(request, f'Sesion programada. Se notifico a {enviados} jugador(es).')
            else:
                messages.success(request, 'Sesion programada. No habia correos de jugadores para notificar.')
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
            entrenamiento = form.save()
            enviados = _enviar_correo_entrenamiento(entrenamiento, creado=False)
            if enviados:
                messages.success(request, f'Entrenamiento actualizado. Se notifico a {enviados} jugador(es).')
            else:
                messages.success(request, 'Entrenamiento actualizado. No habia correos de jugadores para notificar.')
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
        messages.info(request, 'Los entrenamientos quedan en historial fijo y no se eliminan. Puedes editarlo si necesitas corregir datos.')

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
        for entrenamiento in entrenamientos:
            entrenamiento.actualizar_estado(guardar=True)
        _asignar_estado_asistencia_jugador(entrenamientos, jugador)

    return render(request, 'entrenamientos/lista_jugador.html', {
        'entrenamientos': entrenamientos,
        'equipo': equipo,
        'jugador': jugador,
        'entrenamientos_mapa_json': json.dumps(_serializar_entrenamientos_mapa(entrenamientos)),
    })
