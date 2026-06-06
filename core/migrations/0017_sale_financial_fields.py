import django.utils.timezone
from django.db import migrations, models


def migrate_sale_fields(apps, schema_editor):
    Sale = apps.get_model('core', 'Sale')
    for sale in Sale.objects.all().iterator():
        if hasattr(sale, 'name') and sale.name and not getattr(sale, 'concept', None):
            sale.concept = sale.name
        if hasattr(sale, 'price') and sale.price is not None and not getattr(sale, 'amount', None):
            sale.amount = sale.price
        if hasattr(sale, 'observation') and sale.observation and not getattr(sale, 'observations', None):
            sale.observations = sale.observation
        if hasattr(sale, 'created_at') and sale.created_at and not getattr(sale, 'date', None):
            sale.date = sale.created_at.date()
        if not getattr(sale, 'payment_method', None):
            sale.payment_method = 'efectivo'
        if getattr(sale, 'provider', None) is None:
            sale.provider = ''
        sale.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_sale_price_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Monto (S/.)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sale',
            name='concept',
            field=models.CharField(default='', max_length=200, verbose_name='Concepto'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sale',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Fecha'),
        ),
        migrations.AddField(
            model_name='sale',
            name='payment_method',
            field=models.CharField(
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
            ),
        ),
        migrations.AddField(
            model_name='sale',
            name='provider',
            field=models.CharField(blank=True, max_length=200, verbose_name='Proveedor'),
        ),
        migrations.AddField(
            model_name='sale',
            name='observations',
            field=models.TextField(blank=True, verbose_name='Observaciones'),
        ),
        migrations.AddField(
            model_name='sale',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RunPython(migrate_sale_fields, migrations.RunPython.noop),
        migrations.RemoveField(model_name='sale', name='name'),
        migrations.RemoveField(model_name='sale', name='observation'),
        migrations.RemoveField(model_name='sale', name='price'),
        migrations.RemoveField(model_name='sale', name='shift'),
        migrations.RemoveField(model_name='sale', name='size'),
        migrations.AlterModelOptions(
            name='sale',
            options={'ordering': ['-date', '-created_at'], 'verbose_name': 'Venta', 'verbose_name_plural': 'Ventas'},
        ),
    ]
