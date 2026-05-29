from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_shift_active_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='cycle',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ninas_6_9', 'Niñas 6 - 9 años'),
                    ('adolescentes_10_14', 'Adolescentes 10 - 14 años'),
                    ('juvenil_15_plus', 'Juvenil 15 o más'),
                ],
                max_length=20,
                null=True,
                verbose_name='Ciclo',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='student_condition',
            field=models.CharField(
                choices=[
                    ('regular', 'Regular'),
                    ('becado', 'Becado'),
                    ('half_scholarship', '1/2 beca'),
                ],
                default='regular',
                max_length=20,
                verbose_name='Condición del alumno',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='school',
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name='Colegio'),
        ),
        migrations.AddField(
            model_name='student',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[('female', 'Mujer'), ('male', 'Hombre')],
                max_length=10,
                null=True,
                verbose_name='Género',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='size',
            field=models.CharField(
                blank=True,
                choices=[('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L')],
                max_length=5,
                null=True,
                verbose_name='Talla',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='referral_source',
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
                verbose_name='¿Cómo se enteró de la academia?',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='uniform_delivered',
            field=models.BooleanField(default=False, verbose_name='Se entregó uniforme'),
        ),
        migrations.AddField(
            model_name='student',
            name='guardian_dni',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='DNI del apoderado'),
        ),
        migrations.AddField(
            model_name='student',
            name='guardian_birth_date',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de nacimiento del apoderado'),
        ),
        migrations.AddField(
            model_name='student',
            name='guardian_gender',
            field=models.CharField(
                blank=True,
                choices=[('female', 'Mujer'), ('male', 'Hombre')],
                max_length=10,
                null=True,
                verbose_name='Género del apoderado',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='guardian_phone',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Teléfono del apoderado'),
        ),
        migrations.AlterField(
            model_name='student',
            name='contact',
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
                verbose_name='Teléfono del estudiante',
            ),
        ),
        migrations.AlterField(
            model_name='student',
            name='guardian',
            field=models.CharField(
                blank=True,
                max_length=120,
                null=True,
                verbose_name='Nombre del apoderado',
            ),
        ),
    ]
