from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Entrenador, Jugador
from entrenamientos.forms import EntrenamientoForm, obtener_canchas_disponibles
from entrenamientos.models import AsistenciaEntrenamiento, Entrenamiento
from entrenamientos.views import _construir_panel_asistencia, _serializar_entrenamientos_mapa
from inscripciones.models import Cancha, Equipo
from torneos.models import Partido, Torneo


class EntrenamientoDisponibilidadTests(TestCase):
    def setUp(self):
        self.entrenador = Entrenador.objects.create(
            _nombres='Carlos',
            _apellidos='Ruiz',
            _num_documento='12345678',
            _fecha_nacimiento=date(1990, 1, 1),
            _email='carlos@example.com',
            _telefono='3001234567',
            _rol='ENTRENADOR',
            _experiencia='5 anos',
        )
        self.equipo = Equipo.objects.create(
            _nombre='Leones FC',
            _descripcion='Equipo de prueba',
            _anio_fundacion=2010,
            _categoria='SUB14',
            _localidad='Suba',
            _barrio='La Campina',
            entrenador=self.entrenador,
        )
        self.cancha_libre = Cancha.objects.create(
            _nombre_escenario='Cancha Libre',
            _localidad='Suba',
            _barrio='La Campina',
            _direccion_exacta='Calle 1 # 2-3',
            _tipo_disciplina='FUTBOL_11',
            _tipo_superficie='SINTETICA',
            _medidas_area='90x45',
            _estado_conservacion='BUENO',
            _disponibilidad='DISPONIBLE',
        )
        self.cancha_torneo = Cancha.objects.create(
            _nombre_escenario='Cancha Torneo',
            _localidad='Suba',
            _barrio='La Campina',
            _direccion_exacta='Calle 4 # 5-6',
            _tipo_disciplina='FUTBOL_11',
            _tipo_superficie='SINTETICA',
            _medidas_area='90x45',
            _estado_conservacion='BUENO',
            _disponibilidad='DISPONIBLE',
        )
        self.fecha_hora = timezone.now().replace(second=0, microsecond=0) + timedelta(days=2)
        self.torneo = Torneo.objects.create(
            nombre='Torneo Apertura',
            descripcion='Prueba',
            fecha_inicio=self.fecha_hora.date(),
            fecha_fin=self.fecha_hora.date() + timedelta(days=1),
            cupo_maximo=8,
            categoria='SUB14',
            ubicacion='General',
            estado='PROXIMO',
            formato='GRUPOS_SOLO',
        )
        Partido.objects.create(
            torneo=self.torneo,
            equipo_local=self.equipo,
            fase='GRUPOS',
            fecha=self.fecha_hora,
            ubicacion='Cancha Torneo',
            estado='PROGRAMADO',
            jornada=1,
        )

    def test_excluye_canchas_ocupadas_por_torneo(self):
        disponibles = obtener_canchas_disponibles(self.fecha_hora)

        self.assertIn(self.cancha_libre, disponibles)
        self.assertNotIn(self.cancha_torneo, disponibles)

    def test_formulario_rechaza_cancha_ocupada(self):
        form = EntrenamientoForm(data={
            'nombre': 'Sesion intensa',
            'cancha': self.cancha_torneo.pk,
            'fecha_hora': self.fecha_hora.strftime('%Y-%m-%dT%H:%M'),
            'descripcion': 'Trabajo fisico',
        }, fecha_hora=self.fecha_hora)

        self.assertFalse(form.is_valid())
        self.assertIn('cancha', form.errors)

    def test_guardado_copia_nombre_cancha_en_lugar(self):
        form = EntrenamientoForm(data={
            'nombre': 'Sesion tecnica',
            'cancha': self.cancha_libre.pk,
            'fecha_hora': self.fecha_hora.strftime('%Y-%m-%dT%H:%M'),
            'descripcion': 'Control y pase',
        }, fecha_hora=self.fecha_hora)

        self.assertTrue(form.is_valid(), form.errors)
        entrenamiento = form.save(commit=False)
        entrenamiento.equipo = self.equipo
        entrenamiento.entrenador = self.entrenador
        entrenamiento.save()

        self.assertEqual(entrenamiento.lugar, 'Cancha Libre')


class ListaEntrenamientosJugadorMapaTests(TestCase):
    def setUp(self):
        self.entrenador = Entrenador.objects.create(
            _nombres='Laura',
            _apellidos='Suarez',
            _num_documento='87654321',
            _fecha_nacimiento=date(1992, 2, 2),
            _email='laura@example.com',
            _telefono='3007654321',
            _rol='ENTRENADOR',
            _experiencia='8 anos',
        )
        self.equipo = Equipo.objects.create(
            _nombre='Tigres FC',
            _descripcion='Equipo de prueba para mapa',
            _anio_fundacion=2012,
            _categoria='SUB16',
            _localidad='Kennedy',
            _barrio='Britalia',
            entrenador=self.entrenador,
        )
        self.jugador = Jugador.objects.create_user(
            email='jugador@example.com',
            password='clave123',
            _nombres='Mateo',
            _apellidos='Lopez',
            _num_documento='123123123',
            _fecha_nacimiento=date(2010, 5, 5),
            _email='jugador@example.com',
            _telefono='3011234567',
            _rol='JUGADOR',
            _dorsal=10,
            _pie_dominante='derecho',
            _posicion='delantero',
            equipo=self.equipo,
        )
        self.cancha_con_coordenadas = Cancha.objects.create(
            _nombre_escenario='Cancha Mapa',
            _localidad='Kennedy',
            _barrio='Britalia',
            _direccion_exacta='Carrera 80 # 10-20',
            _tipo_disciplina='FUTBOL_11',
            _tipo_superficie='SINTETICA',
            _medidas_area='90x45',
            _estado_conservacion='BUENO',
            _disponibilidad='DISPONIBLE',
            _latitud=4.621,
            _longitud=-74.157,
        )

    def test_serializa_solo_entrenamientos_con_cancha_y_coordenadas(self):
        entrenamiento_con_mapa = Entrenamiento.objects.create(
            nombre='Sesion con mapa',
            descripcion='Trabajo tactico',
            fecha_hora=timezone.now() + timedelta(days=1),
            lugar='Cancha Mapa',
            cancha=self.cancha_con_coordenadas,
            equipo=self.equipo,
            entrenador=self.entrenador,
        )
        Entrenamiento.objects.create(
            nombre='Sesion sin mapa',
            descripcion='Trabajo fisico',
            fecha_hora=timezone.now() + timedelta(days=2),
            lugar='Parque del barrio',
            cancha=None,
            equipo=self.equipo,
            entrenador=self.entrenador,
        )

        data = _serializar_entrenamientos_mapa(
            Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').filter(equipo=self.equipo)
        )

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], entrenamiento_con_mapa.id)
        self.assertEqual(data[0]['cancha'], 'Cancha Mapa')
        self.assertEqual(data[0]['lat'], 4.621)
        self.assertEqual(data[0]['lng'], -74.157)


class AsistenciaEntrenamientoTests(TestCase):
    def setUp(self):
        self.entrenador = Entrenador.objects.create_user(
            email='dt@example.com',
            password='clave123',
            _nombres='Diego',
            _apellidos='Torres',
            _num_documento='456456456',
            _fecha_nacimiento=date(1988, 6, 6),
            _email='dt@example.com',
            _telefono='3021234567',
            _rol='ENTRENADOR',
            _experiencia='10 anos',
        )
        self.equipo = Equipo.objects.create(
            _nombre='Halcones FC',
            _descripcion='Equipo para asistencia',
            _anio_fundacion=2015,
            _categoria='SUB14',
            _localidad='Suba',
            _barrio='Aures',
            entrenador=self.entrenador,
        )
        self.jugador = Jugador.objects.create_user(
            email='asistencia@example.com',
            password='clave123',
            _nombres='Juan',
            _apellidos='Perez',
            _num_documento='789789789',
            _fecha_nacimiento=date(2011, 7, 7),
            _email='asistencia@example.com',
            _telefono='3031234567',
            _rol='JUGADOR',
            _dorsal=7,
            _pie_dominante='derecho',
            _posicion='volante',
            equipo=self.equipo,
        )
        self.entrenamiento = Entrenamiento.objects.create(
            nombre='Sesion de asistencia',
            descripcion='Prueba de marcado',
            fecha_hora=timezone.now() + timedelta(days=1),
            lugar='Cancha central',
            equipo=self.equipo,
            entrenador=self.entrenador,
        )

    def test_entrenador_puede_marcar_asistencia(self):
        self.client.force_login(self.entrenador)
        response = self.client.post(
            reverse('actualizar_asistencia_entrenamiento', args=[self.entrenamiento.id]),
            {
                'jugador_id': self.jugador.id,
                'estado': 'asistio',
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('lista_entrenamientos'))
        asistencia = AsistenciaEntrenamiento.objects.get(
            entrenamiento=self.entrenamiento,
            jugador=self.jugador,
        )
        self.assertIs(asistencia.asistio, True)

    def test_panel_asistencia_resume_estados_por_entrenamiento(self):
        AsistenciaEntrenamiento.objects.create(
            entrenamiento=self.entrenamiento,
            jugador=self.jugador,
            asistio=False,
        )

        panel, total_jugadores = _construir_panel_asistencia(
            Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').filter(equipo=self.equipo),
            self.equipo,
        )

        self.assertEqual(total_jugadores, 1)
        self.assertEqual(len(panel), 1)
        self.assertEqual(panel[0]['entrenamiento'].id, self.entrenamiento.id)
        self.assertEqual(panel[0]['faltaron'], 1)
        self.assertEqual(panel[0]['asistieron'], 0)
        self.assertEqual(panel[0]['confirmados'], 1)
        self.assertEqual(panel[0]['sin_marcar'], 0)
        self.assertEqual(panel[0]['registros'][0]['jugador'].id, self.jugador.id)
        self.assertIs(panel[0]['registros'][0]['estado'], False)
        self.assertEqual(panel[0]['registros'][0]['estado_label'], 'Falto')

    def test_panel_muestra_sin_marcar_cuando_no_hay_registro(self):
        panel, total_jugadores = _construir_panel_asistencia(
            Entrenamiento.objects.select_related('equipo', 'entrenador', 'cancha').filter(equipo=self.equipo),
            self.equipo,
        )

        self.assertEqual(total_jugadores, 1)
        self.assertEqual(panel[0]['sin_marcar'], 1)
        self.assertIsNone(panel[0]['registros'][0]['estado'])
        self.assertEqual(panel[0]['registros'][0]['estado_label'], 'Sin marcar')
