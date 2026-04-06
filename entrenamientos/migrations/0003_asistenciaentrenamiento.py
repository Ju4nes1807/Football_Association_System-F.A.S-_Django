from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_jugador_equipo'),
        ('entrenamientos', '0002_entrenamiento_cancha'),
    ]

    operations = [
        migrations.CreateModel(
            name='AsistenciaEntrenamiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asistio', models.BooleanField(blank=True, null=True)),
                ('fecha_registro', models.DateTimeField(auto_now=True)),
                ('entrenamiento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asistencias_jugadores', to='entrenamientos.entrenamiento')),
                ('jugador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asistencias_entrenamiento', to='accounts.jugador')),
            ],
            options={
                'verbose_name': 'Asistencia de Entrenamiento',
                'verbose_name_plural': 'Asistencias de Entrenamiento',
                'ordering': ['entrenamiento__fecha_hora', 'jugador___dorsal', 'jugador___nombres'],
                'unique_together': {('entrenamiento', 'jugador')},
            },
        ),
    ]
