import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_sale_alter_cycle_options_alter_cycle_slug_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='shift',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sales',
                to='core.shift',
                verbose_name='Turno',
            ),
        ),
        migrations.RemoveField(
            model_name='sale',
            name='category',
        ),
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
    ]
