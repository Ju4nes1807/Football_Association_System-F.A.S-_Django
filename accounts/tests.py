from datetime import date

from django.contrib.auth.hashers import make_password
from django.test import TestCase

from accounts.models import Entrenador, Jugador, Usuario
from inscripciones.models import Equipo


class JugadorMaximoPorEquipoTest(TestCase):
    def setUp(self):
        self.entrenador = Entrenador.objects.create(
            _nombres='Carlos',
            _apellidos='Perez',
            _num_documento='12345678',
            _fecha_nacimiento=date(1990, 1, 1),
            _email='entrenador1@test.com',
            _telefono='3001112233',
            _rol=Usuario.Roles.ENTRENADOR,
            _experiencia='5 anios',
            password=make_password('Tmp12345*'),
        )

        self.equipo = Equipo.objects.create(
            _nombre='Equipo Prueba A',
            _descripcion='',
            _anio_fundacion=2000,
            _categoria=Equipo.Categoria.SUB16,
            _localidad='Suba',
            _barrio='Niza',
            _estado=Equipo.Estado.APROBADO,
            entrenador=self.entrenador,
        )

    def _crear_jugador(self, indice, equipo=None):
        equipo_destino = equipo or self.equipo
        return Jugador.objects.create(
            _nombres=f'Jugador{indice}',
            _apellidos='Prueba',
            _num_documento=str(100000 + indice),
            _fecha_nacimiento=date(2010, 1, 1),
            _email=f'jugador{indice}@test.com',
            _telefono=str(3000000000 + indice),
            _rol=Usuario.Roles.JUGADOR,
            _dorsal=indice,
            _pie_dominante='derecho',
            _posicion='defensa',
            equipo=equipo_destino,
            password=make_password('Tmp12345*'),
        )

    def test_no_permite_superar_30_jugadores_por_equipo(self):
        for i in range(1, 31):
            self._crear_jugador(i)

        with self.assertRaisesMessage(ValueError, 'máximo de 30 jugadores'):
            self._crear_jugador(31)

        self.assertEqual(Jugador.objects.filter(equipo=self.equipo).count(), 30)

    def test_permite_editar_jugador_existente_con_cupo_lleno(self):
        for i in range(1, 31):
            self._crear_jugador(i)

        jugador = Jugador.objects.filter(equipo=self.equipo).first()
        jugador.posicion = 'volante'
        jugador.save()

        self.assertEqual(Jugador.objects.filter(equipo=self.equipo).count(), 30)
        self.assertEqual(jugador.posicion, 'volante')

    def test_no_permite_trasladar_jugador_a_equipo_lleno(self):
        entrenador_2 = Entrenador.objects.create(
            _nombres='Luisa',
            _apellidos='Rojas',
            _num_documento='87654321',
            _fecha_nacimiento=date(1989, 4, 2),
            _email='entrenador2@test.com',
            _telefono='3001112244',
            _rol=Usuario.Roles.ENTRENADOR,
            _experiencia='7 anios',
            password=make_password('Tmp12345*'),
        )
        equipo_2 = Equipo.objects.create(
            _nombre='Equipo Prueba B',
            _descripcion='',
            _anio_fundacion=2002,
            _categoria=Equipo.Categoria.SUB16,
            _localidad='Engativa',
            _barrio='Normandia',
            _estado=Equipo.Estado.APROBADO,
            entrenador=entrenador_2,
        )

        for i in range(1, 31):
            self._crear_jugador(i)

        jugador_equipo_2 = self._crear_jugador(50, equipo=equipo_2)
        jugador_equipo_2.equipo = self.equipo

        with self.assertRaisesMessage(ValueError, 'máximo de 30 jugadores'):
            jugador_equipo_2.save()
