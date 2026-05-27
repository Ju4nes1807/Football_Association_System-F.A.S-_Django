from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.utils import timezone

from accounts.models import Usuario, Entrenador
from inscripciones.models import Equipo, Cancha
from .models import Torneo, InscripcionTorneo, Partido, EstadisticaJugador
from .forms import TorneoForm, PartidoForm

class TorneoModuleTest(TestCase):

    def setUp(self):
        # Configuración básica para las pruebas
        self.entrenador_user = Usuario.objects.create_user(
            email='coach@test.com',
            password='Password123!',
            rol='ENTRENADOR',
            _nombres='Coach',
            _apellidos='Test',
            _num_documento='12345678',
            _fecha_nacimiento=date(1990, 1, 1),
            _telefono='3001112233'
        )
        # El modelo Entrenador usa multi-tabla inheritance con Usuario
        self.entrenador = Entrenador.objects.create(
            usuario_ptr=self.entrenador_user,
            _nombres='Coach',
            _apellidos='Test',
            _num_documento='12345678',
            _fecha_nacimiento=date(1990, 1, 1),
            _telefono='3001112233',
            _email='coach@test.com',
            experiencia=5
        )
        
        self.equipo = Equipo.objects.create(
            nombre='Equipo Test',
            anio_fundacion=2000,
            categoria='MAYOR',
            localidad='Suba',
            barrio='Test',
            entrenador=self.entrenador
        )

        self.cancha = Cancha.objects.create(
            nombre_escenario='Cancha Test',
            localidad='Suba',
            barrio='Test',
            direccion_exacta='Calle 123',
            tipo_disciplina='FUTBOL_11',
            tipo_superficie='SINTETICA',
            medidas_area='90x45',
            estado_conservacion='BUENO'
        )

    def test_torneo_creation(self):
        """Prueba la creación básica de un torneo."""
        torneo = Torneo.objects.create(
            nombre='Torneo de Verano',
            fecha_inicio=date.today() + timedelta(days=10),
            fecha_fin=date.today() + timedelta(days=30),
            cupo_maximo=10,
            categoria='MAYOR',
            ubicacion='Cancha Test - Calle 123'
        )
        self.assertEqual(torneo.nombre, 'Torneo de Verano')
        self.assertEqual(torneo.cupos_disponibles, 10)
        self.assertTrue(torneo.puede_inscribirse)

    def test_torneo_cupos_disponibles(self):
        """Prueba que el cálculo de cupos disponibles sea correcto."""
        torneo = Torneo.objects.create(
            nombre='Torneo Cupos',
            fecha_inicio=date.today() + timedelta(days=10),
            fecha_fin=date.today() + timedelta(days=30),
            cupo_maximo=2,
            categoria='MAYOR',
            ubicacion='Cancha Test - Calle 123'
        )
        
        InscripcionTorneo.objects.create(torneo=torneo, equipo=self.equipo)
        self.assertEqual(torneo.cupos_disponibles, 1)
        
        # Crear otro equipo para llenar el cupo
        otro_user = Usuario.objects.create_user(
            email='other@test.com', 
            password='Password123!', 
            rol='ENTRENADOR',
            _nombres='Other',
            _apellidos='Coach',
            _num_documento='87654321',
            _fecha_nacimiento=date(1995, 5, 5),
            _telefono='3119998877'
        )
        otro_entrenador = Entrenador.objects.create(
            usuario_ptr=otro_user, 
            _nombres='Other',
            _apellidos='Coach',
            _num_documento='87654321',
            _fecha_nacimiento=date(1995, 5, 5),
            _telefono='3119998877',
            _email='other@test.com',
            experiencia=2
        )
        otro_equipo = Equipo.objects.create(
            nombre='Equipo 2', 
            anio_fundacion=2010, 
            entrenador=otro_entrenador, 
            categoria='MAYOR', 
            localidad='Usaquen', 
            barrio='Test'
        )
        
        InscripcionTorneo.objects.create(torneo=torneo, equipo=otro_equipo)
        self.assertEqual(torneo.cupos_disponibles, 0)
        self.assertFalse(torneo.puede_inscribirse)

    def test_torneo_actualizar_estado(self):
        """Prueba que el estado del torneo cambie según la fecha."""
        # Torneo futuro
        t1 = Torneo.objects.create(
            nombre='Torneo Futuro',
            fecha_inicio=date.today() + timedelta(days=5),
            fecha_fin=date.today() + timedelta(days=10),
            categoria='MAYOR',
            ubicacion='Test'
        )
        t1.actualizar_estado()
        self.assertEqual(t1.estado, 'PROXIMO')

        # Torneo en curso (inicio hoy)
        t2 = Torneo.objects.create(
            nombre='Torneo Hoy',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=5),
            categoria='MAYOR',
            ubicacion='Test'
        )
        t2.actualizar_estado()
        self.assertEqual(t2.estado, 'EN_CURSO')

        # Torneo finalizado
        t3 = Torneo.objects.create(
            nombre='Torneo Pasado',
            fecha_inicio=date.today() - timedelta(days=10),
            fecha_fin=date.today() - timedelta(days=5),
            categoria='MAYOR',
            ubicacion='Test'
        )
        t3.actualizar_estado()
        self.assertEqual(t3.estado, 'FINALIZADO')

    def test_torneo_form_validation(self):
        """Prueba las validaciones del formulario de Torneo, incluyendo límites de caracteres."""
        # Caso válido
        data = {
            'nombre': 'Torneo Valido',
            'descripcion': 'Una descripcion corta',
            'fecha_inicio': date.today() + timedelta(days=1),
            'fecha_fin': date.today() + timedelta(days=10),
            'cupo_maximo': '8',
            'categoria': 'MAYOR',
            'formato': 'GRUPOS_SOLO',
            'ubicacion': 'Cancha Test - Calle 123',
            'estado': 'PROXIMO'
        }
        form = TorneoForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

        # Nombre demasiado largo (> 100)
        data['nombre'] = 'A' * 101
        form = TorneoForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

        # Descripción demasiado larga (> 500)
        data['nombre'] = 'Torneo'
        data['descripcion'] = 'B' * 501
        form = TorneoForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('descripcion', form.errors)

        # Fecha fin antes que inicio
        data['descripcion'] = 'Desc'
        data['fecha_fin'] = date.today() - timedelta(days=1)
        form = TorneoForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_fin', form.errors)

    def test_partido_form_same_team_validation(self):
        """Prueba que el formulario de partido no permita que un equipo juegue contra sí mismo."""
        torneo = Torneo.objects.create(
            nombre='Torneo Partidos',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=10),
            categoria='MAYOR',
            ubicacion='Test'
        )
        InscripcionTorneo.objects.create(torneo=torneo, equipo=self.equipo)

        data = {
            'equipo_local': self.equipo.id,
            'equipo_visita': self.equipo.id, # Mismo equipo
            'fase': 'GRUPOS',
            'fecha': timezone.now(),
            'ubicacion': 'Cancha Test',
            'estado': 'PROGRAMADO',
            'jornada': 1
        }
        form = PartidoForm(data=data, torneo=torneo)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(form.errors['__all__'][0], 'El equipo local y el equipo visitante no pueden ser el mismo.')

    def test_inscripcion_duplicada(self):
        """Prueba que un equipo no pueda inscribirse dos veces al mismo torneo."""
        torneo = Torneo.objects.create(
            nombre='Torneo Unico',
            fecha_inicio=date.today() + timedelta(days=1),
            fecha_fin=date.today() + timedelta(days=10),
            categoria='MAYOR',
            ubicacion='Test'
        )
        InscripcionTorneo.objects.create(torneo=torneo, equipo=self.equipo)
        
        with self.assertRaises(Exception): # Debe lanzar IntegrityError por unique_together
            InscripcionTorneo.objects.create(torneo=torneo, equipo=self.equipo)

    def test_partido_fecha_fuera_rango(self):
        """Prueba que un partido no pueda tener una fecha fuera del rango del torneo."""
        inicio = date.today() + timedelta(days=5)
        fin = date.today() + timedelta(days=10)
        torneo = Torneo.objects.create(
            nombre='Torneo Fechas',
            fecha_inicio=inicio,
            fecha_fin=fin,
            categoria='MAYOR',
            ubicacion='Test'
        )
        
        # Fecha antes del inicio
        data = {
            'equipo_local': self.equipo.id,
            'fase': 'GRUPOS',
            'fecha': timezone.make_aware(timezone.datetime.combine(inicio - timedelta(days=1), timezone.datetime.min.time())),
            'ubicacion': 'Test',
            'estado': 'PROGRAMADO',
            'jornada': 1
        }
        form = PartidoForm(data=data, torneo=torneo)
        self.assertFalse(form.is_valid())

    def test_crear_estadistica_jugador(self):
        """Prueba la creación de estadísticas para un jugador en un partido."""
        torneo = Torneo.objects.create(nombre='T1', fecha_inicio=date.today(), fecha_fin=date.today(), categoria='MAYOR', ubicacion='Test')
        partido = Partido.objects.create(torneo=torneo, fecha=timezone.now())
        
        # Crear un jugador con todos los campos obligatorios
        from accounts.models import Jugador
        jugador_user = Usuario.objects.create_user(
            email='player@test.com', 
            password='Password123!', 
            _num_documento='99999999', 
            _fecha_nacimiento=date(2005, 1, 1), 
            _telefono='3009998877', 
            _nombres='Jugador', 
            _apellidos='Prueba'
        )
        jugador = Jugador.objects.create(
            usuario_ptr=jugador_user, 
            _dorsal=10, 
            equipo=self.equipo,
            _nombres='Jugador', 
            _apellidos='Prueba',
            _num_documento='99999999',
            _fecha_nacimiento=date(2005, 1, 1),
            _telefono='3009998877',
            _email='player@test.com'
        )
        
        est = EstadisticaJugador.objects.create(
            partido=partido,
            jugador=jugador,
            equipo=self.equipo,
            goles=2,
            asistencias=1,
            minutos_jugados=90
        )
        self.assertEqual(est.goles, 2)
        self.assertEqual(est.jugador.usuario_ptr.nombres, 'Jugador')

    def test_torneo_cupo_personalizado_liga(self):
        """Prueba que el cupo personalizado solo funcione para el formato de liga y sea par."""
        data = {
            'nombre': 'Torneo Cupo Especial',
            'fecha_inicio': date.today() + timedelta(days=1),
            'fecha_fin': date.today() + timedelta(days=10),
            'cupo_maximo': 'OTRO',
            'cupo_personalizado': 7, # Impar, debe fallar
            'categoria': 'MAYOR',
            'formato': 'GRUPOS_SOLO',
            'ubicacion': 'Cancha Test - Calle 123',
            'estado': 'PROXIMO'
        }
        form = TorneoForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('cupo_personalizado', form.errors)
        
        # Corregir a par
        data['cupo_personalizado'] = 8
        form = TorneoForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
