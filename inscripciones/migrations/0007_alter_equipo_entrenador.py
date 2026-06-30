from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0005_alter_entrenador__experiencia'),
        ('inscripciones', '0006_equipo__motivo_eliminacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipo',
            name='entrenador',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='equipos',
                to='accounts.entrenador',
            ),
        ),
    ]
