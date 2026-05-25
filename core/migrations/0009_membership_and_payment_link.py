from datetime import date, timedelta

from django.db import migrations, models
import django.db.models.deletion


def _default_end(start):
    if start.month == 12:
        return start.replace(year=start.year + 1, month=1, day=start.day)
    try:
        return start.replace(month=start.month + 1)
    except ValueError:
        return start + timedelta(days=30)


def link_payments_to_memberships(apps, schema_editor):
    from django.db.models import Sum

    Student = apps.get_model('core', 'Student')
    Payment = apps.get_model('core', 'Payment')
    Membership = apps.get_model('core', 'Membership')

    for student in Student.objects.all():
        membership = (
            Membership.objects.filter(student_id=student.pk)
            .order_by('-start_date', '-created_at')
            .first()
        )
        if not membership:
            start = student.membership_start or student.enrollment_date or date.today()
            end = student.membership_end or _default_end(start)
            amount = student.monthly_fee or 0
            membership = Membership.objects.create(
                student_id=student.pk,
                start_date=start,
                end_date=end,
                amount_due=amount,
                status='debt',
            )

        Payment.objects.filter(student_id=student.pk, membership__isnull=True).update(
            membership_id=membership.pk
        )

        paid = Payment.objects.filter(membership_id=membership.pk).aggregate(
            total=Sum('amount')
        )['total'] or 0
        membership.status = 'completed' if float(paid) >= float(membership.amount_due) else 'debt'
        membership.save(update_fields=['status'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_student_membership_dates'),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('amount_due', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('debt', 'Deuda'), ('completed', 'Completada')], default='debt', max_length=20)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('renewed_from', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='renewals', to='core.membership')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='core.student')),
            ],
            options={
                'ordering': ['-start_date', '-created_at'],
            },
        ),
        migrations.AddField(
            model_name='payment',
            name='membership',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.membership'),
        ),
        migrations.RunPython(link_payments_to_memberships, migrations.RunPython.noop),
    ]
