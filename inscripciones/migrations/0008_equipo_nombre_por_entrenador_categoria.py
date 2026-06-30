from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('inscripciones', '0007_alter_equipo_entrenador'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipo',
            name='_nombre',
            field=models.CharField(db_column='nombre', max_length=100),
        ),
        migrations.AddConstraint(
            model_name='equipo',
            constraint=models.UniqueConstraint(
                fields=('entrenador', '_nombre', '_categoria'),
                name='equipo_nombre_categoria_por_entrenador_unico',
            ),
        ),
    ]
