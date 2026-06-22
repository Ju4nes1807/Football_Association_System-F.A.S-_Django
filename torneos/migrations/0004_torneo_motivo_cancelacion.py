from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('torneos', '0003_alter_partido_options_partido_fase_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='torneo',
            name='motivo_cancelacion',
            field=models.CharField(blank=True, choices=[
                ('CLIMA', 'Clima o estado de la cancha'),
                ('CUPOS', 'Cupos insuficientes'),
                ('LOGISTICA', 'Problemas logisticos'),
                ('SEGURIDAD', 'Seguridad'),
                ('OTRO', 'Otro motivo'),
            ], max_length=20),
        ),
        migrations.AddField(
            model_name='torneo',
            name='motivo_cancelacion_detalle',
            field=models.TextField(blank=True),
        ),
    ]
