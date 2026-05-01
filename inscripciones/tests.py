from datetime import date, datetime, timedelta
from io import BytesIO
from unittest.mock import patch
import json

from django.core.files.uploadedfile import SimpleUploadedFile
import openpyxl
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Entrenador, Usuario, Jugador
from inscripciones.models import Equipo, Cancha
from inscripciones import views as insc_views

class BaseTestMixin:
    def create_admin(self, idx=1):
        admin = Usuario(
            _nombres='Admin',
            _apellidos=f'Test{idx}',
            _num_documento=f'9000000{idx}',
            _fecha_nacimiento=date(1985, 1, 1),
            _email=f'admin{idx}@test.com',
            _telefono=f'31{idx:08d}',
            _rol=Usuario.Roles.ADMIN,
            is_active=True,
            is_staff=True,
        )
        admin.set_password('Test123*')
        admin.save()
        return admin

    def create_entrenador(self, idx=1):
        entrenador = Entrenador(
            _nombres='Coach',
            _apellidos=f'Test{idx}',
            _num_documento=f'8000000{idx}',
            _fecha_nacimiento=date(1990, 1, 1),
            _email=f'entrenador{idx}@test.com',
            _telefono=f'3{idx:09d}',
            _rol=Usuario.Roles.ENTRENADOR,
            _experiencia='5 anios',
            is_active=True,
        )
        entrenador.set_password('Test123*')
        entrenador.save()
        return entrenador

    def create_jugador(self, idx=1, equipo=None):
        jugador = Jugador(
            _nombres='Jugador',
            _apellidos=f'Test{idx}',
            _num_documento=f'7000000{idx}',
            _fecha_nacimiento=date(2010, 1, 1),
            _email=f'jugador{idx}@test.com',
            _telefono=f'30010000{idx:02d}',
            _rol=Usuario.Roles.JUGADOR,
            _dorsal=10 + idx,
            _pie_dominante='derecho',
            _posicion='defensa',
            equipo=equipo,
            is_active=True,
        )
        jugador.set_password('Test123*')
        jugador.save()
        return jugador

    def create_equipo(self, entrenador, idx=1, **overrides):
        data = {
            '_nombre': f'Equipo {idx}',
            '_descripcion': 'Desc',
            '_anio_fundacion': 2010,
            '_categoria': Equipo.Categoria.SUB12,
            '_localidad': 'Suba',
            '_barrio': 'Niza',
            '_estado': Equipo.Estado.ESPERA,
            'entrenador': entrenador,
        }
        data.update(overrides)
        return Equipo.objects.create(**data)

    def create_cancha(self, idx=1, **overrides):
        data = {
            '_nombre_escenario': f'Cancha {idx}',
            '_localidad': 'Suba',
            '_barrio': 'Niza',
            '_direccion_exacta': 'Calle 1 #2-3',
            '_tipo_disciplina': Cancha.TipoDisciplina.FUTBOL_11,
            '_tipo_superficie': Cancha.TipoSuperficie.SINTETICA,
            '_medidas_area': '90x45',
            '_estado_conservacion': Cancha.EstadoConservacion.BUENO,
            '_capacidad_espectadores': 0,
            '_disponibilidad': Cancha.Disponibilidad.DISPONIBLE,
        }
        data.update(overrides)
        return Cancha.objects.create(**data)


class RegistrarEquipoViewTests(TestCase):
	def setUp(self):
		self.url_registrar = reverse('inscripciones:registrar_equipo')
		self.url_dashboard_admin = reverse('dashboard_admin')
		self.url_mi_equipo = reverse('inscripciones:mi_equipo')

		self.entrenador = self._crear_entrenador(1)
		self.admin = self._crear_admin(1)

	def _crear_entrenador(self, indice):
		entrenador = Entrenador(
			_nombres='Carlos',
			_apellidos=f'Entrenador{indice}',
			_num_documento=f'12345678{indice}',
			_fecha_nacimiento=date(1990, 1, 1),
			_email=f'entrenador{indice}@test.com',
			_telefono=f'3{indice:09d}',
			_rol=Usuario.Roles.ENTRENADOR,
			_experiencia='5 anios',
			is_active=True,
		)
		entrenador.set_password('Test123*')
		entrenador.save()
		return entrenador

	def _crear_admin(self, indice):
		admin = Usuario(
			_nombres='Admin',
			_apellidos=f'Prueba{indice}',
			_num_documento=f'87654321{indice}',
			_fecha_nacimiento=date(1985, 1, 1),
			_email=f'admin{indice}@test.com',
			_telefono=f'31{indice:08d}',
			_rol=Usuario.Roles.ADMIN,
			is_active=True,
			is_staff=True,
		)
		admin.set_password('Test123*')
		admin.save()
		return admin

	def _datos_equipo_validos(self, nombre='Tigres FC'):
		return {
			'nombre': nombre,
			'descripcion': 'Equipo de pruebas',
			'anio_fundacion': 2010,
			'categoria': Equipo.Categoria.SUB12,
			'localidad': 'Suba',
			'barrio': 'La Gaitana',
		}

	def test_redirige_a_dashboard_admin_si_usuario_no_es_entrenador(self):
		self.client.force_login(self.admin)

		response = self.client.get(self.url_registrar)

		self.assertRedirects(response, self.url_dashboard_admin)

	def test_muestra_formulario_a_entrenador_sin_equipo(self):
		self.client.force_login(self.entrenador)

		response = self.client.get(self.url_registrar)

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'inscripciones/registrar_equipo.html')
		self.assertIn('form', response.context)

	def test_redirige_a_mi_equipo_si_entrenador_ya_tiene_equipo(self):
		Equipo.objects.create(
			_nombre='Equipo Existente',
			_descripcion='Con registro previo',
			_anio_fundacion=2012,
			_categoria=Equipo.Categoria.SUB14,
			_localidad='Suba',
			_barrio='Niza',
			_estado=Equipo.Estado.APROBADO,
			entrenador=self.entrenador,
		)

		self.client.force_login(self.entrenador)
		response = self.client.get(self.url_registrar)

		self.assertRedirects(response, self.url_mi_equipo)
		self.assertEqual(Equipo.objects.filter(entrenador=self.entrenador).count(), 1)

	def test_crea_equipo_y_redirige_a_mi_equipo(self):
		self.client.force_login(self.entrenador)

		response = self.client.post(self.url_registrar, data=self._datos_equipo_validos())

		self.assertRedirects(response, self.url_mi_equipo)
		self.assertEqual(Equipo.objects.filter(entrenador=self.entrenador).count(), 1)

		equipo = Equipo.objects.get(entrenador=self.entrenador)
		self.assertEqual(equipo.nombre, 'Tigres FC')
		self.assertEqual(equipo.estado, Equipo.Estado.ESPERA)
		self.assertEqual(equipo.categoria, Equipo.Categoria.SUB12)

	def test_no_crea_equipo_si_nombre_ya_existe(self):
		otro_entrenador = self._crear_entrenador(2)
		Equipo.objects.create(
			_nombre='Tigres FC',
			_descripcion='Equipo ya registrado',
			_anio_fundacion=2005,
			_categoria=Equipo.Categoria.SUB16,
			_localidad='Usaquen',
			_barrio='Cedritos',
			_estado=Equipo.Estado.APROBADO,
			entrenador=otro_entrenador,
		)

		self.client.force_login(self.entrenador)
		response = self.client.post(self.url_registrar, data=self._datos_equipo_validos())

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'inscripciones/registrar_equipo.html')
		self.assertContains(response, 'Ya existe un equipo con ese nombre.')
		self.assertFalse(Equipo.objects.filter(entrenador=self.entrenador).exists())
	
class MiEquipoViewTests(TestCase):
    URL_NAME = 'inscripciones:mi_equipo'
    TEMPLATE = 'inscripciones/mi_equipo.html'

    def setUp(self):
        self.url = reverse(self.URL_NAME)

        self.entrenador = Entrenador(
            _nombres='Juan',
            _apellidos='Pérez',
            _num_documento='123456789',
            _fecha_nacimiento=date(1990, 1, 1),
            _email='entrenador@test.com',
            _telefono='3001234567',
            _rol=Usuario.Roles.ENTRENADOR,
            _experiencia='5 años',
            is_active=True,
        )
        self.entrenador.set_password('Test123*')
        self.entrenador.save()

        self.admin = Usuario(
            _nombres='Admin',
            _apellidos='Test',
            _num_documento='987654321',
            _fecha_nacimiento=date(1985, 1, 1),
            _email='admin@test.com',
            _telefono='3009876543',
            _rol=Usuario.Roles.ADMIN,
            is_active=True,
            is_staff=True,
        )
        self.admin.set_password('Test123*')
        self.admin.save()

    def _get_response_as_entrenador(self):
        self.client.force_login(self.entrenador)
        return self.client.get(self.url)

    def test_redirige_si_no_es_entrenador(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('dashboard_admin'))

    def test_renderiza_equipo_si_entrenador_tiene_equipo(self):
        equipo = Equipo.objects.create(
            _nombre='Equipo Test',
            _descripcion='desc',
            _anio_fundacion=2010,
            _categoria=Equipo.Categoria.SUB12,
            _localidad='Suba',
            _barrio='La Gaitana',
            _estado=Equipo.Estado.APROBADO,
            entrenador=self.entrenador,
        )

        response = self._get_response_as_entrenador()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.TEMPLATE)
        self.assertEqual(response.context['equipo'], equipo)

    def test_renderiza_equipo_none_si_entrenador_sin_equipo(self):
        response = self._get_response_as_entrenador() 

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.TEMPLATE)
        self.assertIsNone(response.context['equipo'])

class ApiViewsTests(TestCase):
    def test_api_localidades(self):
        response = self.client.get(reverse('inscripciones:api_localidades'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('localidades', data)
        self.assertIn('Suba', data['localidades'])
        self.assertEqual(data['localidades'], sorted(data['localidades']))

    def test_api_barrios_con_localidad(self):
        response = self.client.get(reverse('inscripciones:api_barrios'), {'localidad': 'Suba'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('barrios', data)
        self.assertTrue(len(data['barrios']) > 0)
        self.assertEqual(data['barrios'], sorted(data['barrios']))

    def test_api_barrios_sin_localidad(self):
        response = self.client.get(reverse('inscripciones:api_barrios'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'barrios': []})


class EquipoViewsTests(BaseTestMixin, TestCase):
    def setUp(self):
        self.admin = self.create_admin(1)
        self.entrenador = self.create_entrenador(1)
        self.otro_entrenador = self.create_entrenador(2)

    def test_editar_equipo_sin_permiso_redirige(self):
        equipo = self.create_equipo(self.entrenador, idx=1)
        url = reverse('inscripciones:editar_equipo', args=[equipo.id])

        self.client.force_login(self.otro_entrenador)
        response = self.client.get(url)

        self.assertRedirects(response, reverse('inscripciones:mi_equipo'))

    def test_editar_equipo_actualiza(self):
        equipo = self.create_equipo(self.entrenador, idx=1)
        url = reverse('inscripciones:editar_equipo', args=[equipo.id])

        data = {
            'nombre': 'Equipo Nuevo',
            'descripcion': 'Nueva desc',
            'anio_fundacion': 2011,
            'categoria': Equipo.Categoria.SUB14,
            'localidad': 'Suba',
            'barrio': 'Niza',
        }

        self.client.force_login(self.entrenador)
        response = self.client.post(url, data=data)

        self.assertRedirects(response, reverse('inscripciones:mi_equipo'))
        equipo.refresh_from_db()
        self.assertEqual(equipo.nombre, 'Equipo Nuevo')
        self.assertEqual(equipo.estado, Equipo.Estado.ESPERA)

    def test_eliminar_equipo_por_admin(self):
        equipo = self.create_equipo(self.entrenador, idx=1)
        url = reverse('inscripciones:eliminar_equipo', args=[equipo.id])

        self.client.force_login(self.admin)
        response = self.client.post(url)

        self.assertRedirects(response, reverse('inscripciones:lista_equipos'))
        equipo.refresh_from_db()
        self.assertIsNotNone(equipo.eliminar_programada_para)
        self.assertEqual(equipo.motivo_eliminacion, 'Eliminacion programada')

    def test_eliminar_equipo_por_entrenador(self):
        equipo = self.create_equipo(self.entrenador, idx=1)
        url = reverse('inscripciones:eliminar_equipo', args=[equipo.id])

        self.client.force_login(self.entrenador)
        response = self.client.post(url)

        self.assertRedirects(response, reverse('dashboard_entrenador'))
        self.assertFalse(Equipo.objects.filter(id=equipo.id).exists())

    def test_eliminar_equipo_entrenador_bloqueado_si_programado(self):
        equipo = self.create_equipo(
            self.entrenador,
            idx=1,
            _eliminar_programada_para=timezone.now() + timedelta(days=1),
        )
        url = reverse('inscripciones:eliminar_equipo', args=[equipo.id])

        self.client.force_login(self.entrenador)
        response = self.client.post(url)

        self.assertRedirects(response, reverse('inscripciones:mi_equipo'))
        self.assertTrue(Equipo.objects.filter(id=equipo.id).exists())

    def test_eliminar_equipo_aprobado_requiere_motivo(self):
        equipo = self.create_equipo(
            self.entrenador,
            idx=1,
            _estado=Equipo.Estado.APROBADO,
        )
        url = reverse('inscripciones:eliminar_equipo', args=[equipo.id])

        self.client.force_login(self.admin)
        response = self.client.post(url, data={'motivo_eliminacion': ''})

        self.assertRedirects(response, reverse('inscripciones:lista_equipos'))
        equipo.refresh_from_db()
        self.assertIsNone(equipo.eliminar_programada_para)

    def test_eliminar_equipo_aprobado_con_motivo(self):
        equipo = self.create_equipo(
            self.entrenador,
            idx=1,
            _estado=Equipo.Estado.APROBADO,
        )
        url = reverse('inscripciones:eliminar_equipo', args=[equipo.id])

        self.client.force_login(self.admin)
        response = self.client.post(url, data={'motivo_eliminacion': 'Baja solicitada'})

        self.assertRedirects(response, reverse('inscripciones:lista_equipos'))
        equipo.refresh_from_db()
        self.assertIsNotNone(equipo.eliminar_programada_para)
        self.assertEqual(equipo.motivo_eliminacion, 'Baja solicitada')

    def test_eliminar_equipo_no_autorizado(self):
        equipo = self.create_equipo(self.entrenador, idx=1)
        url = reverse('inscripciones:eliminar_equipo', args=[equipo.id])

        self.client.force_login(self.otro_entrenador)
        response = self.client.get(url)

        self.assertRedirects(response, reverse('inscripciones:mi_equipo'))

    def test_lista_equipos_admin_filtra(self):
        self.create_equipo(self.entrenador, idx=1, _nombre='Tigres FC')
        self.create_equipo(self.otro_entrenador, idx=2, _nombre='Leones FC')

        self.client.force_login(self.admin)
        response = self.client.get(reverse('inscripciones:lista_equipos'), {'nombre': 'Tigres'})

        self.assertEqual(response.status_code, 200)
        equipos = list(response.context['equipos'])
        self.assertEqual(len(equipos), 1)
        self.assertEqual(equipos[0].nombre, 'Tigres FC')

    def test_aprobar_equipo(self):
        equipo = self.create_equipo(self.entrenador, idx=1, _motivo_rechazo='x')
        url = reverse('inscripciones:aprobar_equipo', args=[equipo.id])

        self.client.force_login(self.admin)
        response = self.client.post(url, data={'accion': 'aprobar'})

        self.assertRedirects(response, reverse('inscripciones:lista_equipos'))
        equipo.refresh_from_db()
        self.assertEqual(equipo.estado, Equipo.Estado.APROBADO)
        self.assertIsNone(equipo.motivo_rechazo)

    def test_rechazar_equipo_sin_motivo_no_cambia(self):
        equipo = self.create_equipo(self.entrenador, idx=1)
        url = reverse('inscripciones:aprobar_equipo', args=[equipo.id])

        self.client.force_login(self.admin)
        response = self.client.post(url, data={'accion': 'rechazar', 'motivo': ''})

        self.assertRedirects(response, reverse('inscripciones:lista_equipos'))
        equipo.refresh_from_db()
        self.assertEqual(equipo.estado, Equipo.Estado.ESPERA)

    def test_rechazar_equipo_con_motivo(self):
        equipo = self.create_equipo(self.entrenador, idx=1)
        url = reverse('inscripciones:aprobar_equipo', args=[equipo.id])

        self.client.force_login(self.admin)
        response = self.client.post(url, data={'accion': 'rechazar', 'motivo': 'Falta docs'})

        self.assertRedirects(response, reverse('inscripciones:lista_equipos'))
        equipo.refresh_from_db()
        self.assertEqual(equipo.estado, Equipo.Estado.RECHAZADO)
        self.assertEqual(equipo.motivo_rechazo, 'Falta docs')

class JugadorViewsTests(BaseTestMixin, TestCase):
    def setUp(self):
        self.admin = self.create_admin(1)
        self.entrenador = self.create_entrenador(1)
        self.otro_entrenador = self.create_entrenador(2)
        self.equipo_aprobado = self.create_equipo(
            self.entrenador, idx=1, _estado=Equipo.Estado.APROBADO
        )
        self.equipo_pendiente = self.create_equipo(
            self.otro_entrenador, idx=2, _estado=Equipo.Estado.ESPERA
        )

    def _jugador_payload(self, idx=1):
        return {
            'nombres': 'Juan',
            'apellidos': f'Perez{idx}',
            'num_documento': f'1234567{idx}',
            'fecha_nacimiento': '2010-01-01',
            'email': f'jug{idx}@test.com',
            'telefono': f'30011111{idx:02d}',
            'password': 'Test123*',
            'dorsal': 10 + idx,
            'pie_dominante': 'derecho',
            'posicion': 'defensa',
        }

    def test_lista_jugadores_sin_equipo_redirige(self):
        entrenador_sin_equipo = self.create_entrenador(3)
        self.client.force_login(entrenador_sin_equipo)

        response = self.client.get(reverse('inscripciones:lista_jugadores'))

        self.assertRedirects(response, reverse('inscripciones:mi_equipo'))

    def test_lista_jugadores_ok(self):
        self.create_jugador(1, equipo=self.equipo_aprobado)
        self.create_jugador(2, equipo=self.equipo_aprobado)

        self.client.force_login(self.entrenador)
        response = self.client.get(reverse('inscripciones:lista_jugadores'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['jugadores']), 2)

    def test_registrar_jugador_no_entrenador(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('inscripciones:registrar_jugador'))
        self.assertRedirects(response, reverse('dashboard_admin'))

    @patch('inscripciones.forms.validar_edad_categoria', return_value=(True, ''))
    @patch('inscripciones.views._enviar_credenciales_jugador')
    def test_registrar_jugador_ok(self, mock_send, mock_age):
        self.client.force_login(self.entrenador)
        response = self.client.post(
            reverse('inscripciones:registrar_jugador'),
            data=self._jugador_payload(1)
        )

        self.assertRedirects(response, reverse('inscripciones:lista_jugadores'))
        self.assertEqual(Jugador.objects.filter(equipo=self.equipo_aprobado).count(), 1)

    def test_registrar_jugador_equipo_no_aprobado(self):
        self.client.force_login(self.otro_entrenador)
        response = self.client.get(reverse('inscripciones:registrar_jugador'))
        self.assertRedirects(response, reverse('inscripciones:mi_equipo'))

    def test_eliminar_jugador_ok(self):
        jugador = self.create_jugador(1, equipo=self.equipo_aprobado)
        url = reverse('inscripciones:eliminar_jugador', args=[jugador.id])

        self.client.force_login(self.entrenador)
        response = self.client.post(url)

        self.assertRedirects(response, reverse('inscripciones:lista_jugadores'))
        self.assertFalse(Jugador.objects.filter(id=jugador.id).exists())

    def test_editar_jugador_ok(self):
        jugador = self.create_jugador(1, equipo=self.equipo_aprobado)
        url = reverse('inscripciones:editar_jugador', args=[jugador.id])

        self.client.force_login(self.entrenador)
        response = self.client.post(url, data={
            'dorsal': 22,
            'pie_dominante': 'izquierdo',
            'posicion': 'portero',
        })

        self.assertRedirects(response, reverse('inscripciones:lista_jugadores'))
        jugador.refresh_from_db()
        self.assertEqual(jugador.dorsal, 22)
        self.assertEqual(jugador.pie_dominante, 'izquierdo')

    @patch('inscripciones.views.validar_edad_categoria', return_value=(True, ''))
    @patch('inscripciones.views.enviar_credenciales_jugadores_lote')
    def test_carga_masiva_jugadores_ok(self, mock_send, mock_age):
        csv_content = (
            "nombres,apellidos,num_documento,fecha_nacimiento,email,telefono,dorsal,pie_dominante,posicion\n"
            "Juan,Perez,123456789,2010-01-01,j1@test.com,3001111111,10,derecho,defensa\n"
            "Luis,Gomez,123456788,2010-01-02,j2@test.com,3001111112,11,izquierdo,portero\n"
        ).encode('utf-8')
        archivo = SimpleUploadedFile('jugadores.csv', csv_content, content_type='text/csv')

        self.client.force_login(self.entrenador)
        response = self.client.post(
            reverse('inscripciones:carga_masiva_jugadores'),
            data={'archivo': archivo},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Jugador.objects.filter(equipo=self.equipo_aprobado).count(), 2)

    def test_editar_perfil_jugador_ok(self):
        jugador = self.create_jugador(1, equipo=None)
        self.client.force_login(jugador)

        response = self.client.post(reverse('editar_jugador_perfil'), data={
            'nombres': 'Juan',
            'apellidos': 'Lopez',
            'num_documento': '123456789',
            'email': 'nuevo@test.com',
            'telefono': '3002222222',
            'password_actual': 'Test123*',
            'password_nueva': 'NewPass1!',
        })

        self.assertRedirects(response, reverse('editar_jugador_perfil'))
        jugador.refresh_from_db()
        self.assertTrue(jugador.check_password('NewPass1!'))

class CanchaViewsTests(BaseTestMixin, TestCase):
    def setUp(self):
        self.admin = self.create_admin(1)
        self.entrenador = self.create_entrenador(1)

    def _cancha_payload(self, nombre='Cancha 1'):
        return {
            'codigo_idrd': '',
            'nombre_escenario': nombre,
            'localidad': 'Suba',
            'barrio': 'Niza',
            'direccion_exacta': 'Calle 1 #2-3',
            'codigo_rupi': '',
            'tipo_disciplina': Cancha.TipoDisciplina.FUTBOL_11,
            'tipo_superficie': Cancha.TipoSuperficie.SINTETICA,
            'medidas_area': '90x45',
            'estado_conservacion': Cancha.EstadoConservacion.BUENO,
            'tiene_iluminacion': False,
            'tiene_cerramiento': False,
            'capacidad_espectadores': 0,
            'observaciones_tecnicas': '',
        }

    def test_lista_canchas_admin(self):
        self.create_cancha(1, _latitud=1.0, _longitud=2.0)

        self.client.force_login(self.admin)
        response = self.client.get(reverse('inscripciones:lista_canchas'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.context['canchas_json'])
        self.assertEqual(len(data), 1)

    @patch('inscripciones.views.geodificar_direccion', return_value=(1.0, 2.0))
    def test_crear_cancha_ok(self, mock_geo):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('inscripciones:crear_cancha'),
            data=self._cancha_payload('Cancha Nueva'),
        )

        self.assertRedirects(response, reverse('inscripciones:lista_canchas'))
        self.assertTrue(Cancha.objects.filter(_nombre_escenario='Cancha Nueva').exists())

    @patch('inscripciones.views.geodificar_direccion', return_value=(1.0, 2.0))
    def test_editar_cancha_ok(self, mock_geo):
        cancha = self.create_cancha(1)
        url = reverse('inscripciones:editar_cancha', args=[cancha.id])

        self.client.force_login(self.admin)
        response = self.client.post(url, data=self._cancha_payload('Cancha Editada'))

        self.assertRedirects(response, reverse('inscripciones:lista_canchas'))
        cancha.refresh_from_db()
        self.assertEqual(cancha.nombre_escenario, 'Cancha Editada')

    def test_eliminar_cancha_ok(self):
        cancha = self.create_cancha(1)
        url = reverse('inscripciones:eliminar_cancha', args=[cancha.id])

        self.client.force_login(self.admin)
        response = self.client.post(url)

        self.assertRedirects(response, reverse('inscripciones:lista_canchas'))
        self.assertFalse(Cancha.objects.filter(id=cancha.id).exists())

    def test_cambiar_disponibilidad_ok(self):
        cancha = self.create_cancha(1)
        url = reverse('inscripciones:cambiar_disponibilidad', args=[cancha.id])

        self.client.force_login(self.admin)
        response = self.client.post(url, data={'disponibilidad': Cancha.Disponibilidad.OCUPADA})

        self.assertRedirects(response, reverse('inscripciones:lista_canchas'))
        cancha.refresh_from_db()
        self.assertEqual(cancha.disponibilidad, Cancha.Disponibilidad.OCUPADA)

    @patch('inscripciones.views._procesar_fila_cancha', return_value={'ok': True})
    def test_carga_masiva_canchas_ok(self, mock_proc):
        csv_content = (
            "nombre_escenario,localidad,barrio,direccion_exacta,tipo_disciplina,tipo_superficie,medidas_area,estado_conservacion\n"
            "Cancha 1,Suba,Niza,Calle 1 #2-3,futbol 11,sintetica,90x45,bueno\n"
        ).encode('utf-8')
        archivo = SimpleUploadedFile('canchas.csv', csv_content, content_type='text/csv')

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('inscripciones:carga_masiva_canchas'),
            data={'archivo': archivo},
        )

        self.assertEqual(response.status_code, 200)

    def test_lista_canchas_entrenador_solo_disponibles(self):
        self.create_cancha(1, _disponibilidad=Cancha.Disponibilidad.DISPONIBLE, _latitud=1.0, _longitud=2.0)
        self.create_cancha(2, _disponibilidad=Cancha.Disponibilidad.OCUPADA, _latitud=1.0, _longitud=2.0)

        self.client.force_login(self.entrenador)
        response = self.client.get(reverse('inscripciones:lista_canchas_entrenador'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.context['canchas_json'])
        self.assertEqual(len(data), 1)

class HelperFunctionsTests(BaseTestMixin, TestCase):
    def test_get_equipo_entrenador(self):
        entrenador = self.create_entrenador(1)
        equipo = self.create_equipo(entrenador, idx=1)

        user = Usuario.objects.get(pk=entrenador.pk)
        self.assertEqual(insc_views._get_equipo_entrenador(user), equipo)

        admin = self.create_admin(1)
        self.assertIsNone(insc_views._get_equipo_entrenador(admin))

    def test_leer_csv(self):
        csv_content = (
            "nombres,apellidos\n"
            "Juan,Perez\n"
        ).encode('utf-8')
        archivo = SimpleUploadedFile('data.csv', csv_content, content_type='text/csv')

        filas = insc_views._leer_csv(archivo)
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]['nombres'], 'Juan')

    def test_leer_excel(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['nombres', 'apellidos'])
        ws.append(['Juan', 'Perez'])

        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)

        archivo = SimpleUploadedFile(
            'data.xlsx',
            bio.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        filas = insc_views._leer_excel(archivo)
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]['nombres'], 'Juan')

    def test_obtener_valor_fila(self):
        fila = {'a': '', 'b': '  valor '}
        self.assertEqual(insc_views._obtener_valor_fila(fila, ['a', 'b']), 'valor')

    def test_parsear_fecha_nacimiento(self):
        fecha, err = insc_views._parsear_fecha_nacimiento(date(2010, 1, 1))
        self.assertIsNone(err)

        fecha, err = insc_views._parsear_fecha_nacimiento('2010-01-01')
        self.assertIsNone(err)

        fecha, err = insc_views._parsear_fecha_nacimiento('invalida')
        self.assertIsNotNone(err)

    @patch('inscripciones.views.validar_edad_categoria', return_value=(True, ''))
    def test_normalizar_fila_jugador_ok(self, mock_age):
        entrenador = self.create_entrenador(1)
        equipo = self.create_equipo(entrenador, idx=1)

        fila = {
            'nombres': 'Juan',
            'apellidos': 'Perez',
            'num_documento': '123456789',
            'fecha_nacimiento': '2010-01-01',
            'email': 'j1@test.com',
            'telefono': '3001111111',
            'dorsal': '10',
            'pie_dominante': 'derecho',
            'posicion': 'defensa',
        }
        data, error = insc_views._normalizar_fila_jugador(fila, equipo, 2)

        self.assertIsNone(error)
        self.assertEqual(data['dorsal'], 10)

    def test_buscar_existentes_en_bloques(self):
        u1 = self.create_admin(1)
        existentes = insc_views._buscar_existentes_en_bloques(
            Usuario, '_email', {u1.email, 'x@test.com'}
        )
        self.assertIn(u1.email, existentes)
        self.assertNotIn('x@test.com', existentes)

    @patch('inscripciones.views.validar_edad_categoria', return_value=(True, ''))
    @patch('inscripciones.views.enviar_credenciales_jugadores_lote')
    def test_procesar_carga_masiva_jugadores(self, mock_send, mock_age):
        entrenador = self.create_entrenador(1)
        equipo = self.create_equipo(entrenador, idx=1)

        filas = [
            {
                'nombres': 'Juan',
                'apellidos': 'Perez',
                'num_documento': '123456789',
                'fecha_nacimiento': '2010-01-01',
                'email': 'j1@test.com',
                'telefono': '3001111111',
                'dorsal': '10',
                'pie_dominante': 'derecho',
                'posicion': 'defensa',
            },
            {
                'nombres': 'Luis',
                'apellidos': 'Gomez',
                'num_documento': '123456788',
                'fecha_nacimiento': '2010-01-02',
                'email': 'j2@test.com',
                'telefono': '3001111112',
                'dorsal': '11',
                'pie_dominante': 'izquierdo',
                'posicion': 'portero',
            },
        ]

        count, errors = insc_views._procesar_carga_masiva_jugadores(filas, equipo, request=None)
        self.assertEqual(count, 2)
        self.assertEqual(errors, [])
        self.assertEqual(Jugador.objects.filter(equipo=equipo).count(), 2)

    @patch('inscripciones.views.geodificar_direccion', return_value=(1.0, 2.0))
    @patch('inscripciones.views.time.sleep')
    def test_procesar_fila_cancha_ok(self, mock_sleep, mock_geo):
        fila = {
            'nombre_escenario': 'Cancha 1',
            'localidad': 'Suba',
            'barrio': 'Niza',
            'direccion_exacta': 'Calle 1 #2-3',
            'tipo_disciplina': 'futbol 11',
            'tipo_superficie': 'sintetica',
            'medidas_area': '90x45',
            'estado_conservacion': 'bueno',
        }

        result = insc_views._procesar_fila_cancha(fila, 2)
        self.assertTrue(result['ok'])
        self.assertTrue(Cancha.objects.filter(_nombre_escenario='Cancha 1').exists())

    def test_procesar_fila_cancha_faltantes(self):
        fila = {'nombre_escenario': 'Cancha 1'}
        result = insc_views._procesar_fila_cancha(fila, 2)
        self.assertFalse(result['ok'])