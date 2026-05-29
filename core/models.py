from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Shift(models.Model):
    name = models.CharField(max_length=120)
    start_time = models.TimeField()
    end_time = models.TimeField()
    active_days = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    @property
    def code(self):
        return self.pk

    @property
    def schedule(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

    @property
    def active_days_display(self):
        from .weekdays import format_weekdays
        return format_weekdays(self.active_days or [])

    def is_active_on_weekday(self, weekday):
        if weekday is None:
            return True
        days = self.active_days or []
        if not days or len(days) == 7:
            return True
        return weekday in days

    def __str__(self):
        return f"{self.name} ({self.schedule})"


ENROLLMENT_STATUS_CHOICES = [
    ('active', 'Activa'),
    ('inactive', 'Inactiva'),
]

PAYMENT_METHOD_CHOICES = [
    ('efectivo', 'Efectivo'),
    ('transferencia', 'Transferencia'),
    ('tarjeta', 'Tarjeta'),
    ('yape', 'Yape'),
    ('plin', 'Plin'),
    ('otro', 'Otro'),
]

MEMBERSHIP_STATUS_CHOICES = [
    ('debt', 'Deuda'),
    ('completed', 'Completada'),
]

ATTENDANCE_STATUS_CHOICES = [
    ('present', 'Presente'),
    ('absent', 'Ausente'),
    ('late', 'Tarde'),
]

CYCLE_CHOICES = [
    ('ninas_6_9', 'Niñas 6 - 9 años'),
    ('adolescentes_10_14', 'Adolescentes 10 - 14 años'),
    ('juvenil_15_plus', 'Juvenil 15 o más'),
]

STUDENT_CONDITION_CHOICES = [
    ('regular', 'Regular'),
    ('becado', 'Becado'),
    ('half_scholarship', '1/2 beca'),
]

GENDER_CHOICES = [
    ('female', 'Mujer'),
    ('male', 'Hombre'),
]

SIZE_CHOICES = [
    ('XS', 'XS'),
    ('S', 'S'),
    ('M', 'M'),
    ('L', 'L'),
]


class Student(models.Model):
    ENROLLMENT_STATUS_CHOICES = ENROLLMENT_STATUS_CHOICES

    name = models.CharField(max_length=120)
    age = models.PositiveSmallIntegerField(blank=True, null=True)
    dni = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    contact = models.CharField(max_length=200, blank=True, null=True, verbose_name='Teléfono del estudiante')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True, verbose_name='Género')
    cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES, blank=True, null=True, verbose_name='Ciclo')
    student_condition = models.CharField(
        max_length=20,
        choices=STUDENT_CONDITION_CHOICES,
        default='regular',
        verbose_name='Condición del alumno',
    )
    school = models.CharField(max_length=120, blank=True, null=True, verbose_name='Colegio')
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, blank=True, null=True, verbose_name='Talla')
    referral_source = models.CharField(max_length=200, blank=True, null=True, verbose_name='¿Cómo se enteró de la academia?')
    uniform_delivered = models.BooleanField(default=False, verbose_name='Se entregó uniforme')
    guardian = models.CharField(max_length=120, blank=True, null=True, verbose_name='Nombre del apoderado')
    guardian_dni = models.CharField(max_length=15, blank=True, null=True, verbose_name='DNI del apoderado')
    guardian_birth_date = models.DateField(blank=True, null=True, verbose_name='Fecha de nacimiento del apoderado')
    guardian_gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name='Género del apoderado',
    )
    guardian_phone = models.CharField(max_length=200, blank=True, null=True, verbose_name='Teléfono del apoderado')
    address = models.TextField(blank=True, null=True)
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, blank=True, null=True, related_name='students')
    enrollment_status = models.CharField(max_length=10, choices=ENROLLMENT_STATUS_CHOICES, default='active')
    retired = models.BooleanField(default=False)
    retired_reason = models.TextField(blank=True, null=True)
    retired_at = models.DateField(blank=True, null=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    enrollment_date = models.DateField(blank=True, null=True)
    membership_start = models.DateField(blank=True, null=True, verbose_name='Inicio de membresía')
    membership_end = models.DateField(blank=True, null=True, verbose_name='Fin de membresía')
    birth_date = models.DateField(blank=True, null=True)
    attendance_days = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def active(self):
        return not self.retired and self.enrollment_status == 'active'

    @property
    def debt_info(self):
        if not self.monthly_fee or not self.enrollment_date:
            return {'debt': None, 'expected_total': None, 'paid_total': self.payments.aggregate(total=models.Sum('amount'))['total'] or 0, 'months': None}
        from datetime import date
        today = date.today()
        months = (today.year - self.enrollment_date.year) * 12 + today.month - self.enrollment_date.month
        expected_total = months * float(self.monthly_fee)
        paid_total = float(self.payments.aggregate(total=models.Sum('amount'))['total'] or 0)
        debt = max(0, expected_total - paid_total)
        return {'debt': debt, 'expected_total': expected_total, 'paid_total': paid_total, 'months': months}

    @property
    def attendance_days_display(self):
        if self.shift:
            return f'{self.shift.schedule} · {self.shift.active_days_display}'
        labels = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        if not self.attendance_days or len(self.attendance_days) == 7:
            return 'Sin turno'
        return ', '.join([labels[idx] for idx in self.attendance_days if 0 <= idx < len(labels)])

    def attends_on_weekday(self, weekday):
        """Días de clase según el turno (o respaldo en attendance_days si no hay turno)."""
        if self.shift_id:
            return self.shift.is_active_on_weekday(weekday)
        if weekday is None:
            return True
        days = self.attendance_days or []
        if not days or len(days) == 7:
            return True
        return weekday in days

    def _membership_period(self):
        """Devuelve (inicio, fin) usando las fechas del formulario de la alumna."""
        from datetime import timedelta

        if self.membership_start and self.membership_end:
            return self.membership_start, self.membership_end

        membership = self.memberships.filter(
            start_date__lte=timezone.localdate(),
            end_date__gte=timezone.localdate(),
        ).order_by('-end_date').first()
        if not membership:
            membership = self.memberships.order_by('-end_date', '-created_at').first()
        if membership:
            return membership.start_date, membership.end_date

        start = self.membership_start
        end = self.membership_end
        if end and not start:
            start = end - timedelta(days=30)
        return start, end

    @property
    def membership_expiry_info(self):
        """
        Días que faltan para que termine la membresía y color según avance del periodo:
        verde = recién empezó, naranja = mitad, rojo = por terminar o vencida.
        """
        today = timezone.localdate()
        start, end = self._membership_period()
        if not end:
            return {'days': None, 'label': 'Sin membresía', 'color': 'secondary'}
        if not start:
            from datetime import timedelta
            start = end - timedelta(days=30)

        total_days = max((end - start).days, 1)

        if today > end:
            days_left = (end - today).days
            label = f'Vencida hace {abs(days_left)} día{"s" if abs(days_left) != 1 else ""}'
            color = 'danger'
        elif today < start:
            days_left = (end - start).days
            days_until_start = (start - today).days
            if days_left == 0:
                label = 'Inicia hoy'
            else:
                label = f'{days_left} día{"s" if days_left != 1 else ""} (inicia en {days_until_start}d)'
            color = 'success'
        else:
            days_left = (end - today).days
            if days_left == 0:
                label = 'Vence hoy'
                color = 'danger'
            else:
                label = f'{days_left} día{"s" if days_left != 1 else ""}'
                elapsed = (today - start).days
                progress = min(max(elapsed / total_days, 0), 1)
                if progress < 1 / 3:
                    color = 'success'
                elif progress < 2 / 3:
                    color = 'warning'
                else:
                    color = 'danger'

        return {'days': days_left, 'label': label, 'color': color}

    @property
    def membership_days_remaining(self):
        info = self.membership_expiry_info
        return info['days']

    @property
    def membership_days_remaining_display(self):
        return self.membership_expiry_info['label']

    @property
    def whatsapp_url(self):
        if not self.contact:
            return None
        digits = ''.join(ch for ch in self.contact if ch.isdigit())
        if not digits:
            return None

        # Normalize Peruvian mobile numbers if the local number is stored without country code.
        if digits.startswith('00'):
            digits = digits[2:]
        if len(digits) == 9:
            digits = '51' + digits
        elif len(digits) == 10 and digits.startswith('0'):
            digits = '51' + digits[1:]

        if len(digits) < 9:
            return None
        return f'https://wa.me/{digits}'

    def get_shift_display(self):
        if not self.shift:
            return ''
        return str(self.shift)


class Membership(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='memberships')
    start_date = models.DateField()
    end_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=MEMBERSHIP_STATUS_CHOICES, default='debt')
    renewed_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='renewals',
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        return f'{self.student.name} ({self.start_date} - {self.end_date})'

    @property
    def paid_total(self):
        return self.payments.aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def balance(self):
        return max(float(self.amount_due) - float(self.paid_total), 0)

    def recalculate_status(self):
        paid = float(self.paid_total)
        due = float(self.amount_due)
        self.status = 'completed' if paid >= due else 'debt'
        self.save(update_fields=['status'])


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS_CHOICES, default='present')

    class Meta:
        ordering = ['-date']
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.get_status_display()}"


class Payment(models.Model):
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name='payments',
        blank=True,
        null=True,
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='efectivo')

    class Meta:
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if self.membership_id:
            self.student_id = self.membership.student_id
        super().save(*args, **kwargs)
        if self.membership_id:
            self.membership.recalculate_status()

    def __str__(self):
        return f"{self.student.name} - {self.amount} - {self.date}"

class Expense(models.Model):
    date = models.DateField(default=timezone.now, verbose_name='Fecha')
    concept = models.CharField(max_length=200, verbose_name='Concepto')
    provider = models.CharField(max_length=200, blank=True, verbose_name='Proveedor')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto (S/.)')
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='efectivo',
        verbose_name='Medio de pago',
    )
    observations = models.TextField(blank=True, verbose_name='Observaciones')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Egreso'
        verbose_name_plural = 'Egresos'

    def __str__(self):
        return f'{self.date} - {self.concept} - S/ {self.amount}'


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('secretary', 'Secretario'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='secretary')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
