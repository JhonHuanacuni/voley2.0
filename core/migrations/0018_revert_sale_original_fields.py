from django.db import migrations, models
import django.db.models.deletion


def revert_sale_to_original(apps, schema_editor):
    Sale = apps.get_model('core', 'Sale')
    Shift = apps.get_model('core', 'Shift')
    default_shift = Shift.objects.order_by('pk').first()
    for sale in Sale.objects.all().iterator():
        if hasattr(sale, 'concept'):
            sale.name = sale.concept or 'Venta'
        if hasattr(sale, 'amount'):
            sale.price = sale.amount
        if hasattr(sale, 'observations'):
            sale.observation = sale.observations or ''
        if default_shift and not getattr(sale, 'shift_id', None):
            sale.shift_id = default_shift.pk
        sale.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_sale_financial_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='name',
            field=models.CharField(default='', max_length=200, verbose_name='Nombre'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sale',
            name='observation',
            field=models.TextField(blank=True, null=True, verbose_name='Observación'),
        ),
        migrations.AddField(
            model_name='sale',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Precio (S/.)'),
        ),
        migrations.AddField(
            model_name='sale',
            name='shift',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sales',
                to='core.shift',
                verbose_name='Turno',
            ),
        ),
        migrations.AddField(
            model_name='sale',
            name='size',
            field=models.CharField(
                blank=True,
                choices=[('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L')],
                max_length=5,
                null=True,
                verbose_name='Talla',
            ),
        ),
        migrations.RunPython(revert_sale_to_original, migrations.RunPython.noop),
        migrations.RemoveField(model_name='sale', name='amount'),
        migrations.RemoveField(model_name='sale', name='concept'),
        migrations.RemoveField(model_name='sale', name='date'),
        migrations.RemoveField(model_name='sale', name='payment_method'),
        migrations.RemoveField(model_name='sale', name='provider'),
        migrations.RemoveField(model_name='sale', name='observations'),
        migrations.RemoveField(model_name='sale', name='updated_at'),
        migrations.AlterField(
            model_name='sale',
            name='shift',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sales',
                to='core.shift',
                verbose_name='Turno',
            ),
        ),
        migrations.AlterModelOptions(
            name='sale',
            options={'ordering': ['-created_at'], 'verbose_name': 'Venta', 'verbose_name_plural': 'Ventas'},
        ),
    ]
