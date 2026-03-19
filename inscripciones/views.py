from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.db import IntegrityError
from .models import Equipo
from .forms import RegistroEquipoForm, EditarEquipoForm


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

    return render(request, 'inscripciones/lista_equipos.html', {
        'equipos':   equipos,
        'nombre':    nombre,
        'localidad': localidad,
        'estado':    estado,
        'estados':   Equipo.Estado.choices,
        'total':     equipos.count(),
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