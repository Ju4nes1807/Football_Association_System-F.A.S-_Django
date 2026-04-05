from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import Entrenador
from entrenamientos.forms import EntrenamientoForm, obtener_canchas_disponibles
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
