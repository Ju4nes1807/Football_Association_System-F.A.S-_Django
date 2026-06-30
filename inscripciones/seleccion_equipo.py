from django.shortcuts import get_object_or_404

from .models import Equipo


SESSION_EQUIPO_ACTIVO = 'equipo_activo_id'


def equipos_del_entrenador(user):
    entrenador = getattr(user, 'entrenador', None)
    if not entrenador:
        return Equipo.objects.none()
    return Equipo.objects.filter(entrenador=entrenador).order_by('_nombre')


def equipo_activo(request):
    """Devuelve exclusivamente un equipo perteneciente al entrenador autenticado."""
    equipos = equipos_del_entrenador(request.user)
    equipo_id = request.session.get(SESSION_EQUIPO_ACTIVO)
    equipo = equipos.filter(pk=equipo_id).first() if equipo_id else None
    if equipo is None:
        equipo = equipos.first()
        if equipo:
            request.session[SESSION_EQUIPO_ACTIVO] = equipo.pk
        else:
            request.session.pop(SESSION_EQUIPO_ACTIVO, None)
    return equipo


def seleccionar_equipo(request, equipo_id):
    equipo = get_object_or_404(equipos_del_entrenador(request.user), pk=equipo_id)
    request.session[SESSION_EQUIPO_ACTIVO] = equipo.pk
    return equipo
