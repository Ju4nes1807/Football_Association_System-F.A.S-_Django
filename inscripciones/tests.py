from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import Entrenador, Usuario
from inscripciones.models import Equipo


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