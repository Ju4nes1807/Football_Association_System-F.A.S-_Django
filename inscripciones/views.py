from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests
from django.core.paginator import Paginator
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.db import IntegrityError
from .models import Equipo, Cancha
from .forms import RegistroEquipoForm, EditarEquipoForm, RegistroJugadorForm, CargaMasivaJugadoresForm, EditarJugadorEntrenadorForm, EditarPerfilJugadorForm, CanchaForm, CargaMasivaCanchasForm
import csv
import io
from datetime import date, datetime
import openpyxl
from django.contrib.auth.hashers import make_password
from accounts.models import Usuario, Jugador
from django.contrib.auth import update_session_auth_hash
from .utils import validar_edad_categoria, _enviar_credenciales_jugador

def _get_equipo_entrenador(user):
    """Retorna el equipo del entrenador o None."""
    if hasattr(user, 'entrenador'):
        return getattr(user.entrenador, 'equipo', None)
    return None


@login_required
def registrar_equipo(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    if _get_equipo_entrenador(request.user):
        messages.error(request, 'Ya tienes un equipo registrado.')
        return redirect('inscripciones:mi_equipo')

    form = RegistroEquipoForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            try:
                equipo = Equipo()
                equipo.nombre         = data['nombre']
                equipo.descripcion    = data.get('descripcion', '')
                equipo.anio_fundacion = data['anio_fundacion']
                equipo.categoria      = data['categoria']
                equipo.localidad      = data['localidad']
                equipo.barrio         = data['barrio']
                equipo.entrenador     = request.user.entrenador
                equipo.estado         = Equipo.Estado.ESPERA
                if data.get('logo'):
                    equipo.logo = data['logo']
                equipo.save()
                messages.success(request, 'Equipo registrado correctamente. En espera de aprobación.')
                return redirect('inscripciones:mi_equipo')

            except ValueError as e:
                form.add_error(None, str(e))
            except IntegrityError:
                form.add_error('nombre', 'Ya existe un equipo con ese nombre.')

    return render(request, 'inscripciones/registrar_equipo.html', {'form': form})


@login_required
def mi_equipo(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')
    equipo = _get_equipo_entrenador(request.user)
    return render(request, 'inscripciones/mi_equipo.html', {'equipo': equipo})


@login_required
def editar_equipo(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)

    if request.user.rol != 'ENTRENADOR' or equipo.entrenador != request.user.entrenador:
        messages.error(request, 'No tienes permiso para editar este equipo.')
        return redirect('inscripciones:mi_equipo')

    form = EditarEquipoForm(
        request.POST or None,
        request.FILES or None,
        equipo_pk=equipo.id,
        initial={
            'nombre':         equipo.nombre,
            'descripcion':    equipo.descripcion,
            'anio_fundacion': equipo.anio_fundacion,
            'categoria':      equipo.categoria,
            'localidad':      equipo.localidad,
            'barrio':         equipo.barrio,
        }
    )

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            try:
                equipo.nombre         = data['nombre']
                equipo.descripcion    = data.get('descripcion', '')
                equipo.anio_fundacion = data['anio_fundacion']
                equipo.categoria      = data['categoria']
                equipo.localidad      = data['localidad']
                equipo.barrio         = data['barrio']
                if data.get('logo'):
                    equipo.logo = data['logo']
                equipo.estado = Equipo.Estado.ESPERA
                equipo.save()
                messages.success(request, 'Equipo actualizado. En espera de aprobación.')
                return redirect('inscripciones:mi_equipo')

            except ValueError as e:
                form.add_error(None, str(e))
            except IntegrityError:
                form.add_error('nombre', 'Ya existe un equipo con ese nombre.')

    return render(request, 'inscripciones/editar_equipo.html', {
        'form':   form,
        'equipo': equipo,
    })

def api_localidades(request):
    localidades = [
        'Antonio Nariño', 'Barrios Unidos', 'Bosa', 'Chapinero',
        'Ciudad Bolívar', 'Engativá', 'Fontibón', 'Kennedy',
        'La Candelaria', 'Los Mártires', 'Puente Aranda',
        'Rafael Uribe Uribe', 'San Cristóbal', 'Santa Fe',
        'Suba', 'Sumapaz', 'Teusaquillo', 'Tunjuelito',
        'Usaquén', 'Usme'
    ]
    return JsonResponse({'localidades': sorted(localidades)})


def api_barrios(request):
    localidad = request.GET.get('localidad', '')

    barrios = {
        'Usaquén': [
            'Barrancas','Bella Suiza','Bosque Medina','Brizos del Norte',
            'Cedritos','Cedritos Oriental','Cerros de Sotileza','Chicó Norte',
            'Chicó Norte II','Chicó Norte III','Chicó Reservado','Contador',
            'Country Club','El Cedro','El Refugio','El Verbenal','Horizontes',
            'La Cita','La Clarita','La Floresta Norte','La Frontera','La Punta',
            'La Uribe','Las Margaritas','Los Cedros','Los Cedros Oriental',
            'Los Cedros Occidental','Multicentro','Niza Norte','Orquídeas',
            'Paseo del Country','Pradera Norte','San Antonio Norte',
            'San Cristóbal Norte','Santa Ana','Santa Ana Occidental',
            'Santa Ana Oriental','Santa Bárbara','Santa Bárbara Central',
            'Santa Bárbara Occidental','Santa Bárbara Oriental','Soratama',
            'Torca','Toberín','Usaquén','Verbenal','Villa del Prado',
            'Villa Nidia','Vista Hermosa Norte',
        ],
        'Chapinero': [
            'Alcázares Norte','Bosque Calderón','Bosque Calderón Tejada',
            'Chapinero Alto','Chapinero Central','Chapinero Norte',
            'Chicó','Chicó Alto','Chicó Lago','Chicó Lago Occidental',
            'Chicó Reservado','El Castillo','El Paraíso','El Retiro',
            'Granada','Iberia','Juan XXIII','La Cabrera','La Salle',
            'Las Acacias','Las Nieves','Laureles','Los Olivos','Lourdes',
            'Marly','Meissen','Modelo Norte','Muequetá','Navarra',
            'Nueva Autopista','Palacio','Paraíso','Pardo Rubio',
            'Quinta Camacho','Refugio','Rosales','San Isidro Patios',
            'San Luis','San Martín','Sucre','Tejada','Tercer Milenio',
            'Unir I','Unir II',
        ],
        'Santa Fe': [
            'Atanasio Girardot','Bello Horizonte','Belén','Bosque Izquierdo',
            'Egipto','El Guavio','Germania','La Alameda','La Candelaria',
            'La Concordia','La Macarena','Las Aguas','Las Cruces',
            'Las Nieves','Lourdes','Miradores del Muelle','Paloquemao',
            'Paseo Los Libertadores','Ramírez','San Bernardo','San Diego',
            'San Victorino','Santa Bárbara','Santa Inés','Sevilla',
            'Veraguas','Veraguas Central',
        ],
        'San Cristóbal': [
            'Altamira','Arrayanes','Bello Horizonte','Buenos Aires',
            'Córdoba','El Quindío','El Rodeo','El Sosiego','El Triángulo',
            'Esfuerzos Unidos','Guacamayas','La Belleza','La Gloria',
            'La Hortúa','La Victoria','Las Malvinas','Los Alpes',
            'Los Pinos','Luna Park','Manantial','Montebello','Nariño Sur',
            'Nuevo Horizonte','Primero de Mayo','Rafael Uribe',
            'Ramajal','San Blas','San Cristóbal','San Isidro',
            'San Pedro','Santa Inés','Sosiego','Treinta y Un Sur',
            'Veinte de Julio','Villa del Cerro',
        ],
        'Usme': [
            'Alfonso López','Almendra','Armenia','Arrayanes',
            'Betania','Bosques de Bolonia','Brasil','Brazuelos',
            'Chuniza','Ciudad Usme','Comuneros','Compostela',
            'Danubio','El Bosque','El Danubio','El Destino',
            'El Portal','El Tuno','Fiscala','Gran Yomasa',
            'Granjas de San Pablo','Isabel Lleras','La Fiscala',
            'La Flora','La Reforma','Las Violetas','Los Comuneros',
            'Marichuela','Monteblanco','Nuevo Progreso',
            'Parque Entrenubes','Parques de Usme','Pedregal',
            'Porvenir','Puerta al Llano','San Andres',
            'San Isidro','San Libardo','Santa Librada',
            'Tocaimita','Usminia','Villa Alemania','Villa Betania',
            'Villa Consta','Villa Diana','Villa Emilia',
            'Villa Gloria','Yomasa',
        ],
        'Tunjuelito': [
            'Abraham Lincoln','Almendros','Babel','Bello Horizonte',
            'El Campin Sur','El Espino','El Meissen','El Mochuelo',
            'El Perdomo','El Tunal','Fátima','La Fiscala',
            'La Picota','La Quisqueya','Las Colinas','Laguneta',
            'Meissen','Muzú','Nuevo Muzú','Parque Entrenubes',
            'Petroleum','Quiroga','Rafael Uribe','San Benito',
            'San Carlos','Samore','Tunjuelito','Venecia',
            'Villa Gladys','Villa Italia',
        ],
        'Bosa': [
            'Abraham Lincoln','Alameda','Alfonso López','Apogeo',
            'Bella Flor','Bosa','Bosa Central','Bosa Occidental',
            'Brasil','Canoas','Carlos Albán','Casa Grande',
            'Ciudadela El Recreo','Clarelandia','El Eucaliptal',
            'El Porvenir','El Tintal','El Triunfo','El Vapor',
            'Escocia','Estación','Germania','Gran Britalia',
            'Gustavo Restrepo','Honduras','Independencia',
            'Israel','José Antonio Galán','José María Carbonell',
            'La Amistad','La Estancia','La Libertad','La Paz',
            'Las Margaritas','Laureles','Libertad','Llano Oriental',
            'Los Almendros','Metrovivienda','Naranjos','Niza Sur',
            'Nueva Colombia','Nuevo México','Olarte','Orlando Lara',
            'Pablo Neruda','Palermo Sur','Perdomo','Piamonte',
            'Portal de Bosa','Primavera','Recreo','San Bernardino',
            'San Diego','San Eugenio','San Jorge','San José',
            'San Pablo','Santiago de las Atalayas','Santo Domingo',
            'Tintal Norte','Tintal Sur','Villa Claudia','Villa del Río',
            'Villa Emma','Villa Nelly','Vista Hermosa',
        ],
        'Kennedy': [
            'Alquería','Américas','Andes Sur','Antonia Santos',
            'Banderas','Bavaria','Britalia','Calarcá',
            'Carlos Albán','Castilla','Catamarca','Ciudad Kennedy',
            'Ciudad Kennedy Central','Ciudad Kennedy Norte',
            'Ciudad Kennedy Occidental','Ciudad Kennedy Oriental',
            'Ciudad Kennedy Sur','Carvajal','El Amparo',
            'El Arriero','El Claret','El Jazmín','El Listón',
            'El Tingua','El Vergel','Galán','Granjas de Techo',
            'Hipódromo','Independencia','Jazmín','Kennedy',
            'La Alameda','La Alquería','La América','La Igualdad',
            'Las Margaritas','Las Palmeras','Llano Grande',
            'Los Álamos','Los Andes','Lusitania','María Paz',
            'Marsella','Milán','Nuevo Kennedy','Patio Bonito',
            'Perpetuo Socorro','Primavera','Quirigua Sur',
            'Restrepo','San Rafael','Santa Rosita','Santander',
            'Serranías','Timiza','Tintal','Tinto','Tunjuelito',
            'Valladolid','Villa Alsacia','Villa de la Torre',
            'Villa El Dorado','Villa Nelly','Villamar',
        ],
        'Fontibón': [
            'Aeropuerto','Bahía','Bavaria','Bogotá Cundinamarca',
            'Capellanía','Ciudad Salitre Occidental','Ciudad Salitre Oriental',
            'El Muelle','El Recuerdo','El Recuerdo Sur','Emilio Cifuentes',
            'Fontibón','Fontibón Centro','Fontibón San Pablo',
            'Granjas de Techo','Guadual','Kasandra','La Aldea',
            'La Cabaña','La Estancia','La Loma','Las Viñas',
            'Llanitos','Lusitania','Maravillas','Modelia',
            'Modelia Occidental','Modelia Oriental','Montana',
            'Murillo','Prados de Santa Bárbara','Prosperidad',
            'Puerto Horizonte','Rectángulo','Rinconada',
            'San Pablo','Tintal','Tintal Central','Tintal Norte',
            'Tintal Sur','Versalles','Villemar',
        ],
        'Engativá': [
            'Álamos','Álamos Norte','Bachué','Bolivia',
            'Bonanza','Boyacá Real','Brasil','Ciudadela Cafam',
            'Cortijo','Delia','El Muelle','El Palmar',
            'El Rubí','Engativá','Florencia','Francia',
            'Garcés Navas','Garces Navas','Guadalupe','Jardín Botánico',
            'La Cabañita','La Palma','La Pastora','Las Ferias',
            'Las Mercedes','Las Orquídeas','Lombardía','Los Ángeles',
            'Los Cerezos','Luis Carlos Galán','Manuela Beltrán',
            'Minuto de Dios','Morato','Morisco','Navarra',
            'Nueva Esperanza','Palermo','Primavera','Quirigua',
            'Quirigua Norte','Santa Cecilia','Santa Helenita',
            'Santa María del Lago','Sevilla','Tabora',
            'Villa Amalia','Villa Claver','Villa del Mar',
            'Villa Gladys','Villa Luz','Villamaría',
        ],
        'Suba': [
            'Alhambra','Aures','Aures I','Aures II',
            'Bilbao','Britalia','Buenavista','Casa Blanca Suba',
            'Casablanca','Cataluña','Ciudadela Colsubsidio',
            'Compartir','El Prado','El Rincón','Fontanar del Río',
            'Granada Norte','Guicán','Guiparma','Iberia',
            'Jardín de La Esperanza','La Academia','La Alborada',
            'La Campiña','La Conejera','La Esperanza Norte',
            'La Gaitana','La Isabela','La Palma','La Toscana',
            'Las Mercedes','Laureles','Lisboa','Lombardía',
            'Los Arrayanes','Los Naranjos','Mazurén','Niza',
            'Niza Norte','Niza Suba','Nueva Zelandia','Palonegro',
            'Pasadena','Pinar del Río','Potosí','Prado Pinzón',
            'Prado Veraniego','Prado Veraniego Norte',
            'Prado Veraniego Sur','Reserva','Rincón',
            'San Cayetano','San José del Prado','San Pedro de Tibabuyes',
            'Santa Bárbara Occidental','Santa Isabel','Suba',
            'Tibabita','Tibabuyes','Toscana','Villa Cindy',
            'Villa del Prado','Villa Elisa','Villa Hermosa',
        ],
        'Barrios Unidos': [
            '12 de Octubre','Alcázares','Andes Norte','Argentina',
            'Barrios Unidos','Benjamín Herrera','Boyacá','Campincito',
            'Colombia','Comuneros','Coveñas','Doce de Octubre',
            'El Campín','El Rosario','El Triunfo','Gaitán',
            'Jorge Eliécer Gaitán','José Martí','La Castellana',
            'La Esmeralda','La Florida','La Paz','La Patria',
            'Los Andes','Metrópolis','Minuto de Dios','Modelo',
            'Muequetá','Nicolás de Federman','Once de Noviembre',
            'Pablo VI','Palermo','Polo Club','Popular','Pradera',
            'Rionegro','Rioseco','San Fernando','Siete de Agosto',
            'Triangulo','Trinidad Galán','Unión','Veraguas',
        ],
        'Teusaquillo': [
            'Acevedo Tejada','Alameda','Américas','Armenia',
            'Campín','Capri','El Recuerdo','Espartillal',
            'Galerías','Gorgonzola','Hipódromo','La Esmeralda',
            'La Magdalena','La Soledad','Los Alcázares',
            'Maravillas','Marsella','Normandía','Palermo',
            'Parque Nacional','Quinta Paredes','Recuerdo',
            'Sagrado Corazón','San Luis','Santa Fe de Bogotá',
            'Soledad','Teusaquillo','Tibaitata',
        ],
        'Los Mártires': [
            'Colseguros','Eduardo Santos','El Listón','El Vergel',
            'Estación Central','La Favorita','La Pepita','La Sabana',
            'Las Cruces','Laches','Los Mártires','Paloquemao',
            'Ricaurte','San Victorino','Santa Isabel','Santafé',
            'Voto Nacional',
        ],
        'Antonio Nariño': [
            'Antonio Nariño','Ciudad Jardín Sur','Ciudad Berna',
            'Colombia','Cinco Huecos','El Claret','El Eden',
            'El Inglés','El Porvenir','Fatima','La Fragua',
            'Libertador','Muzú','Policarpa','Restrepo',
            'San Antonio','Santa Lucía','Santander',
        ],
        'Puente Aranda': [
            'Alcázares Sur','Alquería','Américas Occidental',
            'Autopista Sur','Batallon Caldas','Camelia',
            'Ciudad Montes','Ciudad Nariño','Colombia',
            'El Rosario','El Salitre','Galán','Jazmín',
            'La Asunción','La Camelia','La Favorita',
            'La Trinidad','Las Américas','Las Delicias',
            'Madelena','Ortezal','Pensilvania','Puente Aranda',
            'Quirigua','Salazar Gómez','Salitre','San Rafael',
            'Santa Matilde','Siete de Agosto','Trinidad',
            'Zona Industrial',
        ],
        'La Candelaria': [
            'Belén','Catedral','Egipto','La Candelaria',
            'Las Aguas','Las Nieves','Santa Bárbara',
        ],
        'Rafael Uribe Uribe': [
            'Bravo Páez','Chircales','Ciudad Jardín Sur',
            'Claret','Consuelo','Corinto','Diana Turbay',
            'El Mochuelo','El Triunfo','Granjas de San Pablo',
            'La Chucua','La Colina','La Flora','La Picota',
            'Laguneta','Llano Oriental','Los Alpes','Marruecos',
            'Marco Fidel Suárez','Molinos','Molinos Norte',
            'Molinos Sur','Olaya','Palermo Sur','Parque Entrenubes',
            'Quiroga','Rafael Uribe','San Agustín','San José',
            'Santa Lucía','Tesoro','Tibanica','Valles de Cafam',
            'Villa del Cerro',
        ],
        'Ciudad Bolívar': [
            'Arborizadora','Arborizadora Alta','Arborizadora Baja',
            'Bella Flor','Canoas','Casa de Teja','Compartir',
            'Danubio Azul','El Espino','El Mochuelo','El Paraíso',
            'El Tesoro','El Triunfo','Escocia','Estrella del Sur',
            'Jerusalén','Juan José Rondón','La Estancia',
            'La Esmeralda','La Gloria','La Isla','La Libertad',
            'La Paz','Las Brisas','Las Manitas','Laguneta',
            'Limonal','Lucero','Lucero Alto','Lucero Bajo',
            'Meissen','México','Minas','Monte Blanco',
            'Monteblanco','Perdomo','Perdomo Alto','Perdomo Bajo',
            'Potosí','Quiba','Quiba Alta','Quiba Baja',
            'Quebradaseca','San Francisco','San Isidro',
            'San Joaquín','San Pedro','Santa Rosita','Sierra Morena',
            'Tesoro','Tres Reyes','Tres Reyes Sur','Verona',
            'Villa Gloria','Vista Hermosa',
        ],
        'Sumapaz': [
            'Betania','Capitolio','Concepción','Erasmo',
            'La Unión','Las Vegas','Los Ríos','Nazareth',
            'Nueva Granada','Raizal','San Antonio','San Juan',
            'Santa Rosa',
        ],
    }

    if not localidad:
        return JsonResponse({'barrios': []})

    lista = barrios.get(localidad, [])
    return JsonResponse({'barrios': sorted(lista)})

@login_required
def eliminar_equipo(request, equipo_id):
    equipo   = get_object_or_404(Equipo, id=equipo_id)
    es_admin = request.user.rol == 'ADMIN'
    es_dueno = (
        request.user.rol == 'ENTRENADOR' and
        hasattr(request.user, 'entrenador') and
        equipo.entrenador == request.user.entrenador
    )

    if not es_admin and not es_dueno:
        messages.error(request, 'No tienes permiso para eliminar este equipo.')
        return redirect('inscripciones:mi_equipo')

    if request.method == 'POST':
        nombre = equipo.nombre
        equipo.delete()
        messages.success(request, f'Equipo "{nombre}" eliminado correctamente.')
        if es_admin:
            return redirect('inscripciones:lista_equipos')
        return redirect('dashboard_entrenador')

    return render(request, 'inscripciones/confirmar_eliminar_equipo.html', {
        'equipo': equipo
    })


@login_required
def lista_equipos(request):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    nombre    = request.GET.get('nombre', '').strip()
    localidad = request.GET.get('localidad', '').strip()
    estado    = request.GET.get('estado', '').strip()

    equipos = Equipo.objects.all().order_by('-fecha_registro')
    if nombre:
        equipos = equipos.filter(_nombre__icontains=nombre)
    if localidad:
        equipos = equipos.filter(_localidad__icontains=localidad)
    if estado:
        equipos = equipos.filter(_estado=estado)
    
    paginator = Paginator(equipos, 12)
    page      = request.GET.get('page')
    equipos   = paginator.get_page(page)

    return render(request, 'inscripciones/lista_equipos.html', {
        'equipos':   equipos,
        'nombre':    nombre,
        'localidad': localidad,
        'estado':    estado,
        'estados':   Equipo.Estado.choices,
        'total': paginator.count,
    })

@login_required
def aprobar_equipo(request, equipo_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    equipo = get_object_or_404(Equipo, id=equipo_id)
    accion = request.POST.get('accion')

    if accion == 'aprobar':
        equipo.estado         = Equipo.Estado.APROBADO
        equipo.motivo_rechazo = None  # ← limpiar si había uno previo
        messages.success(request, f'Equipo "{equipo.nombre}" aprobado.')

    elif accion == 'rechazar':
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, 'Debes indicar el motivo del rechazo.')
            return redirect('inscripciones:lista_equipos')
        equipo.estado         = Equipo.Estado.RECHAZADO
        equipo.motivo_rechazo = motivo
        messages.error(request, f'Equipo "{equipo.nombre}" rechazado.')

    equipo.save()
    return redirect('inscripciones:lista_equipos')

@login_required
def lista_jugadores(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')
    
    equipo = _get_equipo_entrenador(request.user)
    if not equipo:
        messages.error(request, 'No tienes un equipo registrado.')
        return redirect ('inscripciones:mi_equipo')
    
    jugadores = Jugador.objects.filter(equipo = equipo).order_by('_dorsal')
    return render(request, 'inscripciones/lista_jugadores.html', {'equipo': equipo, 'jugadores': jugadores})

@login_required
def registrar_jugador(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    equipo = _get_equipo_entrenador(request.user)
    if not equipo:
        messages.error(request, 'Debes registrar un equipo primero.')
        return redirect('inscripciones:mi_equipo')

    if equipo.estado != 'APROBADO':
        messages.error(request, 'Tu equipo debe estar aprobado para registrar jugadores.')
        return redirect('inscripciones:mi_equipo')

    form = RegistroJugadorForm(request.POST or None, equipo=equipo)

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            jugador = Jugador()
            jugador.nombres          = data['nombres']
            jugador.apellidos        = data['apellidos']
            jugador.num_documento    = data['num_documento']
            jugador.fecha_nacimiento = data['fecha_nacimiento']
            jugador.email            = data['email']
            jugador.telefono         = data['telefono']
            jugador._rol             = Usuario.Roles.JUGADOR
            jugador.dorsal           = data['dorsal']
            jugador.pie_dominante    = data['pie_dominante']
            jugador.posicion         = data['posicion']
            jugador.equipo           = equipo
            jugador.set_password(data['password'])
            jugador.save()

            _enviar_credenciales_jugador(jugador, data['password'], request)

            messages.success(request, f'Jugador {data["nombres"]} registrado correctamente.')
            return redirect('inscripciones:lista_jugadores')

        except IntegrityError as e:
            # Mapear la constraint violada al campo correspondiente
            error = str(e).lower()
            if 'email' in error or '_email' in error:
                form.add_error('email', 'Este correo ya está registrado.')
            elif 'num_documento' in error or '_num_documento' in error:
                form.add_error('num_documento', 'Este documento ya está registrado.')
            elif 'telefono' in error or '_telefono' in error:
                form.add_error('telefono', 'Este teléfono ya está registrado.')
            elif 'dorsal' in error or '_dorsal' in error:
                form.add_error('dorsal', f'El dorsal ya está en uso en este equipo.')
            else:
                form.add_error(None, f'Error de integridad en base de datos: {e}')

        except ValueError as e:
            form.add_error(None, str(e))

    return render(request, 'inscripciones/registrar_jugador.html', {
        'form': form,
        'equipo': equipo,
    })

@login_required
def eliminar_jugador(request, jugador_id):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    jugador = get_object_or_404(Jugador, id=jugador_id)
    equipo  = _get_equipo_entrenador(request.user)

    if jugador.equipo != equipo:
        messages.error(request, 'No tienes permiso para eliminar este jugador.')
        return redirect('inscripciones:lista_jugadores')

    if request.method == 'POST':
        nombre = f'{jugador.nombres} {jugador.apellidos}'
        jugador.delete()
        messages.success(request, f'Jugador "{nombre}" eliminado.')
        return redirect('inscripciones:lista_jugadores')

    return render(request, 'inscripciones/confirmar_eliminar_jugador.html', {
        'jugador': jugador
    })

@login_required
def carga_masiva_jugadores(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    equipo = _get_equipo_entrenador(request.user)
    if not equipo:
        messages.error(request, 'Debes registrar un equipo primero.')
        return redirect('inscripciones:mi_equipo')

    if equipo.estado != 'APROBADO':
        messages.error(request, 'Tu equipo debe estar aprobado para registrar jugadores.')
        return redirect('inscripciones:mi_equipo')

    form = CargaMasivaJugadoresForm(request.POST or None, request.FILES or None)
    errores  = []
    exitosos = 0

    if request.method == 'POST' and form.is_valid():
        archivo = form.cleaned_data['archivo']
        nombre  = archivo.name.lower()

        try:
            if nombre.endswith('.xlsx'):
                filas = _leer_excel(archivo)
            else:
                filas = _leer_csv(archivo)

            for i, fila in enumerate(filas, start=2):
                resultado = _procesar_fila_jugador(fila, equipo, i, request)
                if resultado['ok']:
                    exitosos += 1
                else:
                    errores.append(resultado['error'])

            if exitosos:
                messages.success(request, f'{exitosos} jugador(es) registrado(s) correctamente.')
            if errores:
                messages.error(request, f'{len(errores)} fila(s) con errores.')

        except Exception as e:
            messages.error(request, f'Error procesando el archivo: {str(e)}')

    return render(request, 'inscripciones/carga_masiva_jugadores.html', {
        'form':    form,
        'errores': errores,
        'equipo':  equipo,
    })

def _leer_excel(archivo):
    wb   = openpyxl.load_workbook(archivo)
    ws   = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).strip().lower() if h else '' for h in rows[0]]
    filas   = []
    for row in rows[1:]:
        if any(cell is not None for cell in row):
            filas.append(dict(zip(headers, row)))
    return filas


def _leer_csv(archivo):
    content = archivo.read().decode('utf-8-sig')
    reader  = csv.DictReader(io.StringIO(content))
    return [
        {k.strip().lower(): v for k, v in row.items()}
        for row in reader
    ]


def _procesar_fila_jugador(fila, equipo, num_fila, request):
    try:
        # Mapeo flexible de columnas
        def get(keys):
            for k in keys:
                if k in fila and fila[k] not in (None, ''):
                    return str(fila[k]).strip()
            return ''

        nombres          = get(['nombres', 'nombre'])
        apellidos        = get(['apellidos', 'apellido'])
        num_documento    = get(['num_documento', 'documento', 'cedula'])
        fecha_str        = get(['fecha_nacimiento', 'fecha nacimiento', 'nacimiento'])
        email            = get(['email', 'correo'])
        telefono         = get(['telefono', 'teléfono', 'celular'])
        dorsal_str       = get(['dorsal', 'numero', 'número'])
        pie_dominante    = get(['pie_dominante', 'pie dominante', 'pie'])
        posicion         = get(['posicion', 'posición'])
        password         = get(['password', 'contraseña', 'clave']) or 'Fas2024*'

        # Validaciones básicas
        campos_requeridos = {
            'nombres': nombres, 'apellidos': apellidos,
            'num_documento': num_documento, 'fecha_nacimiento': fecha_str,
            'email': email, 'telefono': telefono,
            'dorsal': dorsal_str, 'pie_dominante': pie_dominante,
            'posicion': posicion,
        }
        faltantes = [k for k, v in campos_requeridos.items() if not v]
        if faltantes:
            return {'ok': False, 'error': f'Fila {num_fila}: Campos vacíos: {", ".join(faltantes)}'}

        # Parsear fecha
        fecha_val = fila.get('fecha_nacimiento') or fila.get('fecha nacimiento') or fila.get('nacimiento')

        if isinstance(fecha_val, (datetime, date)):
            fecha_nacimiento = fecha_val.date() if isinstance(fecha_val, datetime) else fecha_val
        elif isinstance(fecha_val, str):
            fecha_str = fecha_val.strip()
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'):
                try:
                    fecha_nacimiento = datetime.strptime(fecha_str, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                return {'ok': False, 'error': f'Fila {num_fila}: Fecha inválida "{fecha_str}"'}
        else:
            return {'ok': False, 'error': f'Fila {num_fila}: Fecha inválida o vacía'}

        # Validar edad vs categoría
        valido, msg = validar_edad_categoria(fecha_nacimiento, equipo.categoria)
        if not valido:
            return {'ok': False, 'error': f'Fila {num_fila}: {msg}'}

        # Validar duplicados
        if Usuario.objects.filter(_email=email).exists():
            return {'ok': False, 'error': f'Fila {num_fila}: Correo "{email}" ya registrado'}
        if Usuario.objects.filter(_num_documento=num_documento).exists():
            return {'ok': False, 'error': f'Fila {num_fila}: Documento "{num_documento}" ya registrado'}
        if Usuario.objects.filter(_telefono=telefono).exists():
            return {'ok': False, 'error': f'Fila {num_fila}: Teléfono "{telefono}" ya registrado'}

        dorsal = int(dorsal_str)
        if Jugador.objects.filter(equipo=equipo, _dorsal=dorsal).exists():
            return {'ok': False, 'error': f'Fila {num_fila}: Dorsal {dorsal} ya en uso'}

        # Crear jugador
        jugador = Jugador()
        jugador.nombres          = nombres
        jugador.apellidos        = apellidos
        jugador.num_documento    = num_documento
        jugador.fecha_nacimiento = fecha_nacimiento
        jugador.email            = email
        jugador.telefono         = telefono
        jugador._rol             = Usuario.Roles.JUGADOR
        jugador.dorsal           = dorsal
        jugador.pie_dominante    = pie_dominante.lower()
        jugador.posicion         = posicion.lower()
        jugador.equipo           = equipo
        jugador.set_password(password)
        jugador.save()

        _enviar_credenciales_jugador(jugador, password, request)

        return {'ok': True}

    except Exception as e:
        return {'ok': False, 'error': f'Fila {num_fila}: {str(e)}'}

@login_required
def editar_jugador(request, jugador_id):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    jugador = get_object_or_404(Jugador, id=jugador_id)
    equipo  = _get_equipo_entrenador(request.user)

    if jugador.equipo != equipo:
        messages.error(request, 'No tienes permiso para editar este jugador.')
        return redirect('inscripciones:lista_jugadores')

    form = EditarJugadorEntrenadorForm(
        request.POST or None,
        jugador_pk=jugador.id,
        equipo=equipo,
        initial={
            'dorsal':        jugador.dorsal,
            'pie_dominante': jugador.pie_dominante,
            'posicion':      jugador.posicion,
        }
    )

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            try:
                jugador.dorsal        = data['dorsal']
                jugador.pie_dominante = data['pie_dominante']
                jugador.posicion      = data['posicion']
                jugador.save()
                messages.success(request, 'Jugador actualizado correctamente.')
                return redirect('inscripciones:lista_jugadores')
            except ValueError as e:
                form.add_error(None, str(e))

    return render(request, 'inscripciones/editar_jugador.html', {
        'form':    form,
        'jugador': jugador,
        'equipo':  equipo,
    })

@login_required
def editar_perfil_jugador(request):
    if request.user.rol != 'JUGADOR':
        return redirect('dashboard_entrenador')

    user = request.user
    form = EditarPerfilJugadorForm(
        request.POST or None,
        jugador_pk=user.id,
        initial={
            'nombres':       user.nombres,
            'apellidos':     user.apellidos,
            'num_documento': user.num_documento,
            'email':         user.email,
            'telefono':      user.telefono,
        }
    )

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            try:
                user.nombres       = data['nombres']
                user.apellidos     = data['apellidos']
                user.num_documento = data['num_documento']
                user.email         = data['email']
                user.telefono      = data['telefono']

                password_actual = data.get('password_actual')
                password_nueva  = data.get('password_nueva')
                if password_actual and password_nueva:
                    if user.check_password(password_actual):
                        user.set_password(password_nueva)
                        update_session_auth_hash(request, user)
                        messages.success(request, 'Contraseña actualizada.')
                    else:
                        form.add_error('password_actual', 'Contraseña actual incorrecta.')
                        return render(request, 'accounts/roles/editar_perfil_jugador.html', {'form': form})

                user.save()
                messages.success(request, 'Perfil actualizado correctamente.')
                return redirect('editar_jugador_perfil')

            except ValueError as e:
                form.add_error(None, str(e))
            except IntegrityError as e:
                err = str(e).lower()
                if 'email' in err:
                    form.add_error('email', 'Este correo ya está registrado.')
                elif 'documento' in err:
                    form.add_error('num_documento', 'Este documento ya está registrado.')
                elif 'telefono' in err:
                    form.add_error('telefono', 'Este teléfono ya está registrado.')

    return render(request, 'accounts/roles/editar_perfil_jugador.html', {'form': form})

@login_required
def lista_canchas(request):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    nombre       = request.GET.get('nombre', '').strip()
    localidad    = request.GET.get('localidad', '').strip()
    disciplina   = request.GET.get('disciplina', '').strip()
    disponibilidad = request.GET.get('disponibilidad', '').strip()

    canchas = Cancha.objects.all().order_by('_nombre_escenario')
    if nombre:
        canchas = canchas.filter(_nombre_escenario__icontains=nombre)
    if localidad:
        canchas = canchas.filter(_localidad__icontains=localidad)
    if disciplina:
        canchas = canchas.filter(_tipo_disciplina=disciplina)
    if disponibilidad:
        canchas = canchas.filter(_disponibilidad=disponibilidad)
    
    paginator = Paginator(canchas, 15)
    page      = request.GET.get('page')
    canchas   = paginator.get_page(page)

    return render(request, 'inscripciones/canchas/lista_canchas.html', {
        'canchas':        canchas,
        'total': paginator.count,
        'nombre':         nombre,
        'localidad':      localidad,
        'disciplina':     disciplina,
        'disponibilidad': disponibilidad,
        'disciplinas':    Cancha.TipoDisciplina.choices,
        'disponibilidades': Cancha.Disponibilidad.choices,
    })


# ── Crear cancha ──
@login_required
def crear_cancha(request):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    form = CanchaForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            try:
                cancha = Cancha()
                cancha.codigo_idrd            = data.get('codigo_idrd')
                cancha.nombre_escenario       = data['nombre_escenario']
                cancha.localidad              = data['localidad']
                cancha.barrio                 = data['barrio']
                cancha.direccion_exacta       = data['direccion_exacta']
                cancha.codigo_rupi            = data.get('codigo_rupi')
                cancha.tipo_disciplina        = data['tipo_disciplina']
                cancha.tipo_superficie        = data['tipo_superficie']
                cancha.medidas_area           = data['medidas_area']
                cancha.estado_conservacion    = data['estado_conservacion']
                cancha.tiene_iluminacion      = data.get('tiene_iluminacion', False)
                cancha.tiene_cerramiento      = data.get('tiene_cerramiento', False)
                cancha.capacidad_espectadores = data['capacidad_espectadores']
                cancha.observaciones_tecnicas = data.get('observaciones_tecnicas')
                cancha.save()
                messages.success(request, f'Cancha "{cancha.nombre_escenario}" registrada correctamente.')
                return redirect('inscripciones:lista_canchas')
            except ValueError as e:
                form.add_error(None, str(e))

    return render(request, 'inscripciones/canchas/form_cancha.html', {
        'form':   form,
        'titulo': 'Registrar Cancha',
        'accion': 'Registrar',
    })


# ── Editar cancha ──
@login_required
def editar_cancha(request, cancha_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    cancha = get_object_or_404(Cancha, id=cancha_id)
    form   = CanchaForm(
        request.POST or None,
        initial={
            'codigo_idrd':            cancha.codigo_idrd,
            'nombre_escenario':       cancha.nombre_escenario,
            'localidad':              cancha.localidad,
            'barrio':                 cancha.barrio,
            'direccion_exacta':       cancha.direccion_exacta,
            'codigo_rupi':            cancha.codigo_rupi,
            'tipo_disciplina':        cancha.tipo_disciplina,
            'tipo_superficie':        cancha.tipo_superficie,
            'medidas_area':           cancha.medidas_area,
            'estado_conservacion':    cancha.estado_conservacion,
            'tiene_iluminacion':      cancha.tiene_iluminacion,
            'tiene_cerramiento':      cancha.tiene_cerramiento,
            'capacidad_espectadores': cancha.capacidad_espectadores,
            'observaciones_tecnicas': cancha.observaciones_tecnicas,
        }
    )

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            try:
                cancha.codigo_idrd            = data.get('codigo_idrd')
                cancha.nombre_escenario       = data['nombre_escenario']
                cancha.localidad              = data['localidad']
                cancha.barrio                 = data['barrio']
                cancha.direccion_exacta       = data['direccion_exacta']
                cancha.codigo_rupi            = data.get('codigo_rupi')
                cancha.tipo_disciplina        = data['tipo_disciplina']
                cancha.tipo_superficie        = data['tipo_superficie']
                cancha.medidas_area           = data['medidas_area']
                cancha.estado_conservacion    = data['estado_conservacion']
                cancha.tiene_iluminacion      = data.get('tiene_iluminacion', False)
                cancha.tiene_cerramiento      = data.get('tiene_cerramiento', False)
                cancha.capacidad_espectadores = data['capacidad_espectadores']
                cancha.observaciones_tecnicas = data.get('observaciones_tecnicas')
                cancha.save()
                messages.success(request, 'Cancha actualizada correctamente.')
                return redirect('inscripciones:lista_canchas')
            except ValueError as e:
                form.add_error(None, str(e))

    return render(request, 'inscripciones/canchas/form_cancha.html', {
        'form':   form,
        'cancha': cancha,
        'titulo': 'Editar Cancha',
        'accion': 'Guardar cambios',
    })


# ── Eliminar cancha ──
@login_required
def eliminar_cancha(request, cancha_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    cancha = get_object_or_404(Cancha, id=cancha_id)

    if request.method == 'POST':
        nombre = cancha.nombre_escenario
        cancha.delete()
        messages.success(request, f'Cancha "{nombre}" eliminada.')
        return redirect('inscripciones:lista_canchas')

    return render(request, 'inscripciones/canchas/confirmar_eliminar_cancha.html', {
        'cancha': cancha
    })


# ── Cambiar disponibilidad ──
@login_required
def cambiar_disponibilidad(request, cancha_id):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    cancha = get_object_or_404(Cancha, id=cancha_id)

    if request.method == 'POST':
        nueva = request.POST.get('disponibilidad')
        try:
            cancha.disponibilidad = nueva
            cancha.save()
            messages.success(request, f'Disponibilidad actualizada a "{cancha.disponibilidad_display}".')
        except ValueError as e:
            messages.error(request, str(e))

    return redirect('inscripciones:lista_canchas')


# ── Carga masiva ──
@login_required
def carga_masiva_canchas(request):
    if request.user.rol != 'ADMIN':
        return redirect('dashboard_entrenador')

    form     = CargaMasivaCanchasForm(request.POST or None, request.FILES or None)
    errores  = []
    exitosos = 0

    if request.method == 'POST' and form.is_valid():
        archivo = form.cleaned_data['archivo']
        nombre  = archivo.name.lower()
        try:
            if nombre.endswith('.xlsx'):
                filas = _leer_excel(archivo)
            else:
                filas = _leer_csv(archivo)

            for i, fila in enumerate(filas, start=2):
                resultado = _procesar_fila_cancha(fila, i)
                if resultado['ok']:
                    exitosos += 1
                else:
                    errores.append(resultado['error'])

            if exitosos:
                messages.success(request, f'{exitosos} cancha(s) registrada(s) correctamente.')
            if errores:
                messages.error(request, f'{len(errores)} fila(s) con errores.')

        except Exception as e:
            messages.error(request, f'Error procesando el archivo: {str(e)}')

    return render(request, 'inscripciones/canchas/carga_masiva_canchas.html', {
        'form':    form,
        'errores': errores,
    })


def _procesar_fila_cancha(fila, num_fila):
    try:
        def get(keys):
            for k in keys:
                if k in fila and fila[k] not in (None, ''):
                    return str(fila[k]).strip()
            return ''

        nombre_escenario      = get(['nombre_escenario', 'nombre'])
        localidad             = get(['localidad'])
        barrio                = get(['barrio'])
        direccion_exacta      = get(['direccion_exacta', 'direccion'])
        tipo_disciplina       = get(['tipo_disciplina', 'disciplina'])
        tipo_superficie       = get(['tipo_superficie', 'superficie'])
        medidas_area          = get(['medidas_area', 'medidas'])
        estado_conservacion   = get(['estado_conservacion', 'estado'])
        capacidad_str         = get(['capacidad_espectadores', 'capacidad']) or '0'
        codigo_idrd           = get(['codigo_idrd', 'codigo'])
        codigo_rupi           = get(['codigo_rupi', 'rupi'])
        tiene_iluminacion     = get(['tiene_iluminacion', 'iluminacion']).lower() in ('si', 'sí', 'true', '1', 'yes')
        tiene_cerramiento     = get(['tiene_cerramiento', 'cerramiento']).lower() in ('si', 'sí', 'true', '1', 'yes')
        observaciones         = get(['observaciones_tecnicas', 'observaciones'])

        campos_requeridos = {
            'nombre_escenario':    nombre_escenario,
            'localidad':           localidad,
            'barrio':              barrio,
            'direccion_exacta':    direccion_exacta,
            'tipo_disciplina':     tipo_disciplina,
            'tipo_superficie':     tipo_superficie,
            'medidas_area':        medidas_area,
            'estado_conservacion': estado_conservacion,
        }
        faltantes = [k for k, v in campos_requeridos.items() if not v]
        if faltantes:
            return {'ok': False, 'error': f'Fila {num_fila}: Campos vacíos: {", ".join(faltantes)}'}

        # Mapeo flexible de valores
        disciplina_map = {
            'futbol 11': 'FUTBOL_11', 'fútbol 11': 'FUTBOL_11',
            'futbol 8':  'FUTBOL_8',  'fútbol 8':  'FUTBOL_8',
            'futbol 5':  'FUTBOL_5',  'fútbol 5':  'FUTBOL_5',
            'microfutbol': 'MICROFUTBOL', 'microfútbol': 'MICROFUTBOL',
        }
        superficie_map = {
            'sintetica':      'SINTETICA',
            'sintética':      'SINTETICA',
            'natural':        'NATURAL',
            'arena':          'ARENA',
            'cemento':        'CEMENTO',
            'dura':           'CEMENTO',
            'cemento (dura)': 'CEMENTO',
            'cemento (duro)': 'CEMENTO',
        }
        conservacion_map = {
            'bueno': 'BUENO', 'regular': 'REGULAR',
            'malo':  'MALO',  'critico': 'CRITICO', 'crítico': 'CRITICO',
        }

        tipo_disciplina_val    = disciplina_map.get(tipo_disciplina.lower(), tipo_disciplina.upper())
        tipo_superficie_val    = superficie_map.get(tipo_superficie.lower(), tipo_superficie.upper())
        estado_conservacion_val = conservacion_map.get(estado_conservacion.lower(), estado_conservacion.upper())

        cancha = Cancha()
        cancha.codigo_idrd            = codigo_idrd or None
        cancha.nombre_escenario       = nombre_escenario
        cancha.localidad              = localidad
        cancha.barrio                 = barrio
        cancha.direccion_exacta       = direccion_exacta
        cancha.codigo_rupi            = codigo_rupi or None
        cancha.tipo_disciplina        = tipo_disciplina_val
        cancha.tipo_superficie        = tipo_superficie_val
        cancha.medidas_area           = medidas_area
        cancha.estado_conservacion    = estado_conservacion_val
        cancha.tiene_iluminacion      = tiene_iluminacion
        cancha.tiene_cerramiento      = tiene_cerramiento
        cancha.capacidad_espectadores = int(float(capacidad_str)) if capacidad_str else 0
        cancha.observaciones_tecnicas = observaciones or None
        cancha.save()

        return {'ok': True}

    except Exception as e:
        return {'ok': False, 'error': f'Fila {num_fila}: {str(e)}'}


# ── Lista canchas entrenador — solo lectura ──
@login_required
def lista_canchas_entrenador(request):
    if request.user.rol != 'ENTRENADOR':
        return redirect('dashboard_admin')

    nombre     = request.GET.get('nombre', '').strip()
    localidad  = request.GET.get('localidad', '').strip()
    disciplina = request.GET.get('disciplina', '').strip()

    canchas = Cancha.objects.filter(
        _disponibilidad=Cancha.Disponibilidad.DISPONIBLE
    ).order_by('_nombre_escenario')

    if nombre:
        canchas = canchas.filter(_nombre_escenario__icontains=nombre)
    if localidad:
        canchas = canchas.filter(_localidad__icontains=localidad)
    if disciplina:
        canchas = canchas.filter(_tipo_disciplina=disciplina)

    paginator = Paginator(canchas, 12)  # ← mayúscula
    page      = request.GET.get('page')
    canchas   = paginator.get_page(page)

    return render(request, 'inscripciones/canchas/lista_canchas_entrenador.html', {
        'canchas':     canchas,
        'total':       paginator.count,  # ← desde paginator, no canchas.count()
        'nombre':      nombre,
        'localidad':   localidad,
        'disciplina':  disciplina,
        'disciplinas': Cancha.TipoDisciplina.choices,
    })