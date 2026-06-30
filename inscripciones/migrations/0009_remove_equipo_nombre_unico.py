from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('inscripciones', '0008_equipo_nombre_por_entrenador_categoria'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='equipo',
            name='equipo_nombre_categoria_por_entrenador_unico',
        ),
    ]
