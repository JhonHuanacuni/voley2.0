from django.db import migrations, models
import django.db.models.deletion


CYCLE_SEED = [
    ('ninas_6_9', 'Niñas 6 - 9 años', 0),
    ('adolescentes_10_14', 'Adolescentes 10 - 14 años', 1),
    ('juvenil_15_plus', 'Juvenil 15 o más', 2),
]


def seed_cycles(apps, schema_editor):
    Cycle = apps.get_model('core', 'Cycle')
    for slug, name, sort_order in CYCLE_SEED:
        Cycle.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'sort_order': sort_order, 'is_active': True},
        )


def link_students_to_cycles(apps, schema_editor):
    Student = apps.get_model('core', 'Student')
    Cycle = apps.get_model('core', 'Cycle')
    for student in Student.objects.exclude(cycle_old='').exclude(cycle_old=None):
        cycle = Cycle.objects.filter(slug=student.cycle_old).first()
        if cycle:
            student.cycle_link_id = cycle.pk
            student.save(update_fields=['cycle_link_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_expense'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Nombre')),
                ('slug', models.SlugField(max_length=40, unique=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('sort_order', models.PositiveSmallIntegerField(default=0, verbose_name='Orden')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Ciclo',
                'verbose_name_plural': 'Ciclos',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.RunPython(seed_cycles, migrations.RunPython.noop),
        migrations.RenameField(
            model_name='student',
            old_name='cycle',
            new_name='cycle_old',
        ),
        migrations.AddField(
            model_name='student',
            name='cycle_link',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='core.cycle',
                verbose_name='Ciclo',
            ),
        ),
        migrations.RunPython(link_students_to_cycles, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='student',
            name='cycle_old',
        ),
        migrations.RenameField(
            model_name='student',
            old_name='cycle_link',
            new_name='cycle',
        ),
        migrations.AlterField(
            model_name='student',
            name='cycle',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='students',
                to='core.cycle',
                verbose_name='Ciclo',
            ),
        ),
    ]
