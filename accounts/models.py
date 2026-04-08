from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# Create your models here.
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
class Usuario(AbstractBaseUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        ENTRENADOR = 'ENTRENADOR', 'Entrenador'
        JUGADOR = 'JUGADOR', 'Jugador'

    _nombres = models.CharField(max_length=50, db_column='nombres')
    _apellidos = models.CharField(max_length=50, db_column='apellidos')
    _num_documento = models.CharField(max_length = 12, unique=True, db_column='num_documento')
    _fecha_nacimiento = models.DateField(db_column='fecha_nacimiento')
    _email = models.EmailField(unique=True, db_column='email')
    _telefono = models.CharField(unique=True, max_length=20, db_column='telefono')
    _rol = models.CharField(max_length=15, choices=Roles.choices, default = Roles.ADMIN, db_column='rol')

    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)

    USERNAME_FIELD = '_email'
    REQUIRED_FIELDS = ['_nombres', '_apellidos', '_num_documento']

    objects = UsuarioManager()

    # ── Nombres ──
    @property
    def nombres(self):
        return self._nombres

    @nombres.setter
    def nombres(self, value):
        if not value or len(value.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres.')
        self._nombres = value.strip()

    # ── Apellidos ──
    @property
    def apellidos(self):
        return self._apellidos

    @apellidos.setter
    def apellidos(self, value):
        if not value or len(value.strip()) < 2:
            raise ValueError('Los apellidos deben tener al menos 2 caracteres.')
        self._apellidos = value.strip()

    # ── Documento ──
    @property
    def num_documento(self):
        return self._num_documento

    @num_documento.setter
    def num_documento(self, value):
        import re
        if not re.match(r'^\d{6,12}$', str(value).strip()):
            raise ValueError('El documento debe tener entre 6 y 12 dígitos.')
        self._num_documento = value.strip()

    # ── Fecha nacimiento ──
    @property
    def fecha_nacimiento(self):
        return self._fecha_nacimiento

    @fecha_nacimiento.setter
    def fecha_nacimiento(self, value):
        from datetime import date
        if value > date.today():
            raise ValueError('La fecha no puede ser futura.')
        self._fecha_nacimiento = value

    # ── Email ──
    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        import re
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', value):
            raise ValueError('Correo electrónico inválido.')
        self._email = value.lower().strip()

    # ── Teléfono ──
    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, value):
        import re
        if not re.match(r'^3[0-9]{9}$', str(value).strip()):
            raise ValueError('Teléfono colombiano inválido (ej: 3001234567).')
        self._telefono = value.strip()

    # ── Rol ──
    @property
    def rol(self):
        return self._rol

    @rol.setter
    def rol(self, value):
        roles_validos = [r[0] for r in self.Roles.choices]
        if value not in roles_validos:
            raise ValueError(f'Rol inválido. Opciones: {roles_validos}')
        self._rol = value

class Jugador(Usuario):
    MAX_JUGADORES_POR_EQUIPO = 30

    _dorsal = models.PositiveIntegerField(db_column='dorsal')
    _pie_dominante = models.CharField(max_length=20, db_column='pie_dominante')
    _posicion = models.CharField(max_length=50, db_column='posicion')
    equipo = models.ForeignKey('inscripciones.Equipo', on_delete = models.CASCADE, null = True, blank = True, related_name = 'jugadores')

    # ── Dorsal ──
    @property
    def dorsal(self):
        return self._dorsal

    @dorsal.setter
    def dorsal(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError('El dorsal debe ser un número positivo.')
        if value > 99:
            raise ValueError('El dorsal no puede ser mayor a 99.')
        self._dorsal = value

    # ── Pie dominante ──
    @property
    def pie_dominante(self):
        return self._pie_dominante

    @pie_dominante.setter
    def pie_dominante(self, value):
        opciones = ['derecho', 'izquierdo', 'ambos']
        if not value or value.lower().strip() not in opciones:
            raise ValueError(f'Pie dominante inválido. Opciones: {opciones}')
        self._pie_dominante = value.lower().strip()

    # ── Posicion ──
    @property
    def posicion(self):
        return self._posicion

    @posicion.setter
    def posicion(self, value):
        posiciones_validas = [
            'portero', 'defensa', 'lateral derecho', 'lateral izquierdo',
            'central', 'mediocampista', 'volante', 'extremo derecho',
            'extremo izquierdo', 'delantero', 'centrodelantero'
        ]
        if not value or value.lower().strip() not in posiciones_validas:
            raise ValueError(f'Posición inválida. Opciones: {posiciones_validas}')
        self._posicion = value.lower().strip()

    def _validar_cupo_equipo(self):
        if not self.equipo_id:
            return

        jugadores_equipo = Jugador.objects.filter(equipo_id=self.equipo_id)
        if self.pk:
            jugadores_equipo = jugadores_equipo.exclude(pk=self.pk)

        if jugadores_equipo.count() >= self.MAX_JUGADORES_POR_EQUIPO:
            raise ValueError(
                f'El equipo ya alcanzó el máximo de {self.MAX_JUGADORES_POR_EQUIPO} jugadores.'
            )

    def save(self, *args, **kwargs):
        self._validar_cupo_equipo()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"

class Entrenador(Usuario):
    _experiencia = models.CharField(max_length=15, db_column='experiencia')

    @property
    def experiencia(self):
        return self._experiencia

    @experiencia.setter
    def experiencia(self, value):
        if not value or not str(value).strip():
            raise ValueError('La experiencia es obligatoria.')
        self._experiencia = str(value).strip()

    class Meta:
        verbose_name = "Entrenador"
        verbose_name_plural = "Entrenadores"