from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_student_extended_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Fecha')),
                ('concept', models.CharField(max_length=200, verbose_name='Concepto')),
                ('provider', models.CharField(blank=True, max_length=200, verbose_name='Proveedor')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto (S/.)')),
                ('payment_method', models.CharField(
                    choices=[
                        ('efectivo', 'Efectivo'),
                        ('transferencia', 'Transferencia'),
                        ('tarjeta', 'Tarjeta'),
                        ('yape', 'Yape'),
                        ('plin', 'Plin'),
                        ('otro', 'Otro'),
                    ],
                    default='efectivo',
                    max_length=20,
                    verbose_name='Medio de pago',
                )),
                ('observations', models.TextField(blank=True, verbose_name='Observaciones')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Egreso',
                'verbose_name_plural': 'Egresos',
                'ordering': ['-date', '-created_at'],
            },
        ),
    ]
