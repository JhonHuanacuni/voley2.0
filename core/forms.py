from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.forms import DateInput
from datetime import date
from .models import (
    Attendance,
    Cycle,
    Expense,
    Membership,
    PAYMENT_METHOD_CHOICES,
    Payment,
    Sale,
    Shift,
    Student,
    UserProfile,
)
from .weekdays import WEEKDAY_ORDER_MON_FIRST


class StudentForm(forms.ModelForm):
    cycle = forms.ModelChoiceField(
        queryset=Cycle.objects.none(),
        empty_label='Seleccione ciclo',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Ciclo',
        required=False,
    )
    shift = forms.ModelChoiceField(
        queryset=Shift.objects.none(),
        empty_label='SELECCIONE TURNO',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Turno',
        required=False,
    )

    birth_date = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d'],
        label='Fecha de nacimiento',
    )

    guardian_birth_date = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d'],
        label='Fecha de nacimiento del apoderado',
    )

    enrollment_date = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Fecha de inscripción',
    )

    membership_start = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Fecha de inicio de membresía',
    )

    membership_end = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Fecha final de membresía',
    )

    uniform_delivered = forms.BooleanField(
        required=False,
        label='Se entregó uniforme',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = Student
        fields = [
            'name',
            'dni',
            'birth_date',
            'age',
            'gender',
            'email',
            'contact',
            'cycle',
            'student_condition',
            'school',
            'size',
            'shift',
            'address',
            'enrollment_status',
            'monthly_fee',
            'enrollment_date',
            'membership_start',
            'membership_end',
            'referral_source',
            'uniform_delivered',
            'guardian',
            'guardian_dni',
            'guardian_birth_date',
            'guardian_gender',
            'guardian_phone',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo de la alumna'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Edad'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono del estudiante'}),
            'cycle': forms.Select(attrs={'class': 'form-control'}),
            'student_condition': forms.Select(attrs={'class': 'form-control'}),
            'school': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Colegio'}),
            'size': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Dirección', 'rows': 2}),
            'enrollment_status': forms.Select(attrs={'class': 'form-control'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cuota mensual'}),
            'referral_source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. redes sociales, referido, volante',
            }),
            'guardian': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del apoderado'}),
            'guardian_dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI del apoderado'}),
            'guardian_gender': forms.Select(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono del apoderado'}),
        }
        labels = {
            'name': 'Nombre completo',
            'dni': 'DNI',
            'age': 'Edad',
            'gender': 'Género',
            'email': 'Email',
            'contact': 'Teléfono del estudiante',
            'cycle': 'Ciclo',
            'student_condition': 'Condición del alumno',
            'school': 'Colegio',
            'size': 'Talla',
            'shift': 'Turno',
            'address': 'Dirección',
            'birth_date': 'Fecha de nacimiento',
            'enrollment_status': 'Estado de matrícula',
            'monthly_fee': 'Cuota mensual',
            'enrollment_date': 'Fecha de inscripción',
            'membership_start': 'Inicio de membresía',
            'membership_end': 'Fin de membresía',
            'referral_source': '¿Cómo se enteró de la academia?',
            'guardian': 'Nombre del apoderado',
            'guardian_dni': 'DNI del apoderado',
            'guardian_gender': 'Género del apoderado',
            'guardian_phone': 'Teléfono del apoderado',
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('membership_start')
        end = cleaned.get('membership_end')
        if start and end and end < start:
            self.add_error(
                'membership_end',
                'La fecha final de membresía no puede ser anterior a la de inicio.',
            )
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        is_new = not getattr(self.instance, 'pk', None)
        if is_new and not self.is_bound:
            self.fields['enrollment_date'].initial = date.today().isoformat()
            self.fields['membership_start'].initial = date.today().isoformat()

        date_fields = (
            'birth_date',
            'enrollment_date',
            'membership_start',
            'membership_end',
            'guardian_birth_date',
        )
        if self.instance and self.instance.pk:
            for field_name in date_fields:
                value = getattr(self.instance, field_name, None)
                if value:
                    self.fields[field_name].initial = value.isoformat()

        self.fields['shift'].queryset = Shift.objects.order_by('name')
        self.fields['shift'].help_text = 'El horario y los días de clase se toman del turno seleccionado.'
        self.fields['cycle'].queryset = Cycle.objects.filter(is_active=True).order_by('name')
        if self.instance and self.instance.pk and self.instance.cycle_id:
            from django.db.models import Q
            self.fields['cycle'].queryset = Cycle.objects.filter(
                Q(is_active=True) | Q(pk=self.instance.cycle_id),
            ).order_by('name').distinct()
        self.fields['gender'].empty_label = 'Seleccione'
        self.fields['guardian_gender'].empty_label = 'Seleccione'
        self.fields['size'].empty_label = 'Seleccione talla'

    def save(self, commit=True):
        student = super().save(commit=False)
        if student.shift_id:
            student.attendance_days = list(student.shift.active_days or WEEKDAY_ORDER_MON_FIRST)
        if commit:
            student.save()
        return student


class MembershipForm(forms.ModelForm):
    student_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    student_search = forms.CharField(
        required=False,
        label='Buscar alumna',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escriba nombre o DNI (mín. 3 caracteres)',
            'autocomplete': 'off',
            'id': 'student-search',
        }),
    )

    start_date = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Inicio de membresía',
    )
    end_date = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Fin de membresía',
    )

    class Meta:
        model = Membership
        fields = ['start_date', 'end_date', 'amount_due', 'notes']
        widgets = {
            'amount_due': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monto a pagar'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'amount_due': 'Monto de la membresía',
            'notes': 'Notas',
        }

    def __init__(self, *args, **kwargs):
        self.student_instance = kwargs.pop('student_instance', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['student_id'].initial = self.instance.student_id
            self.fields['student_search'].initial = self._student_label(self.instance.student)
            for field_name in ('start_date', 'end_date'):
                value = getattr(self.instance, field_name, None)
                if value:
                    self.fields[field_name].initial = value.isoformat()
        elif self.student_instance:
            self.fields['student_id'].initial = self.student_instance.pk
            self.fields['student_search'].initial = self._student_label(self.student_instance)
            if not self.is_bound:
                fee = self.student_instance.monthly_fee
                if fee:
                    self.fields['amount_due'].initial = fee

    @staticmethod
    def _student_label(student):
        parts = [student.name]
        if student.dni:
            parts.append(f'DNI: {student.dni}')
        return ' — '.join(parts)

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'La fecha final no puede ser anterior al inicio.')
        student_id = cleaned.get('student_id')
        if not student_id and not (self.instance and self.instance.pk):
            self.add_error('student_search', 'Seleccione una alumna de la lista.')
        return cleaned

    def save(self, commit=True):
        membership = super().save(commit=False)
        if not membership.student_id:
            membership.student_id = self.cleaned_data['student_id']
        if commit:
            membership.save()
            membership.recalculate_status()
        return membership


class MembershipRenewForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Nuevo inicio',
    )
    end_date = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Nuevo fin',
    )
    payment_amount = forms.DecimalField(
        required=False,
        min_value=0,
        label='Monto del pago (opcional)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00',
        }),
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        required=False,
        initial='efectivo',
        label='Método de pago',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Membership
        fields = ['start_date', 'end_date', 'amount_due', 'notes']
        widgets = {
            'amount_due': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'amount_due': 'Monto de la membresía',
            'notes': 'Notas',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('start_date', 'end_date'):
            if self.instance and self.instance.pk:
                value = getattr(self.instance, field_name, None)
            elif self.initial.get(field_name):
                value = self.initial.get(field_name)
            else:
                value = None
            if value and hasattr(value, 'isoformat'):
                self.fields[field_name].initial = value.isoformat()
            elif value:
                self.fields[field_name].initial = value

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get('payment_amount')
        if amount is not None and amount <= 0:
            cleaned['payment_amount'] = None
        return cleaned


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'student': 'Alumna',
            'date': 'Fecha',
            'status': 'Estado',
        }


class ShiftForm(forms.ModelForm):
    active_days = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input form-check-input-lg'}),
        required=False,
        label='Días habilitados',
    )

    class Meta:
        model = Shift
        fields = ['name', 'start_time', 'end_time', 'active_days']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del turno'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        labels = {
            'name': 'Nombre del turno',
            'start_time': 'Hora de inicio',
            'end_time': 'Hora de fin',
        }

    def __init__(self, *args, **kwargs):
        from .weekdays import WEEKDAY_CHOICES_MON_FIRST, sort_weekdays
        super().__init__(*args, **kwargs)
        self.fields['active_days'].choices = WEEKDAY_CHOICES_MON_FIRST
        if not self.is_bound:
            if self.instance.pk and self.instance.active_days:
                self.fields['active_days'].initial = sort_weekdays(self.instance.active_days)
            else:
                self.fields['active_days'].initial = list(WEEKDAY_ORDER_MON_FIRST)

    def clean_active_days(self):
        from .weekdays import sort_weekdays
        days = self.cleaned_data.get('active_days') or []
        if not days:
            return list(WEEKDAY_ORDER_MON_FIRST)
        return sort_weekdays([int(d) for d in days])


class CycleForm(forms.ModelForm):
    class Meta:
        model = Cycle
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Niñas 6 - 9 años'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nombre del ciclo',
            'is_active': 'Activo',
        }


class PaymentCreateForm(forms.ModelForm):
    student_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    student_search = forms.CharField(
        required=False,
        label='Estudiante',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar estudiante ...',
            'autocomplete': 'off',
            'id': 'payment-student-search',
        }),
    )
    confirm_new_membership = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_confirm_new_membership'}),
        initial='',
    )
    date = forms.DateField(
        widget=DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Fecha',
    )

    class Meta:
        model = Payment
        fields = ['date', 'amount', 'method']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monto'}),
            'method': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'amount': 'Monto',
            'method': 'Método',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            from django.utils import timezone
            self.fields['date'].initial = timezone.localdate().isoformat()

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('student_id'):
            self.add_error('student_search', 'Seleccione un estudiante de la lista.')
        return cleaned


class PaymentForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Fecha',
    )

    class Meta:
        model = Payment
        fields = ['membership', 'date', 'amount', 'method']
        widgets = {
            'membership': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monto'}),
            'method': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'membership': 'Membresía',
            'amount': 'Monto',
            'method': 'Método',
        }

    def __init__(self, *args, **kwargs):
        membership_qs = kwargs.pop('membership_qs', None)
        super().__init__(*args, **kwargs)
        if membership_qs is not None:
            self.fields['membership'].queryset = membership_qs
        if self.instance and self.instance.pk and self.instance.date:
            self.fields['date'].initial = self.instance.date.isoformat()


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'concept', 'provider', 'amount', 'payment_method', 'observations']
        widgets = {
            'date': DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d',
            ),
            'concept': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Alquiler cancha'}),
            'provider': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del proveedor'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas adicionales'}),
        }
        labels = {
            'date': 'Fecha',
            'concept': 'Concepto',
            'provider': 'Proveedor',
            'amount': 'Monto (S/.)',
            'payment_method': 'Medio de pago',
            'observations': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        date_field = self.fields['date']
        date_field.input_formats = ['%Y-%m-%d']
        if self.instance.pk and self.instance.date:
            date_field.widget.attrs['value'] = self.instance.date.strftime('%Y-%m-%d')


class SaleForm(forms.ModelForm):
    shift = forms.ModelChoiceField(
        queryset=Shift.objects.none(),
        empty_label='Seleccione turno',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Turno',
    )

    class Meta:
        model = Sale
        fields = ['name', 'shift', 'size', 'price', 'observation']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto/servicio'}),
            'size': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'observation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observación'}),
        }
        labels = {
            'name': 'Nombre',
            'size': 'Talla',
            'price': 'Precio',
            'observation': 'Observación',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shift'].queryset = Shift.objects.order_by('name')
        self.fields['size'].empty_label = 'Seleccione talla'


class SystemUserCreateForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Usuario',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
    )
    first_name = forms.CharField(
        required=False,
        label='Nombres',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
    )
    last_name = forms.CharField(
        required=False,
        label='Apellidos',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
    )
    email = forms.EmailField(
        required=False,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
    )
    password_confirm = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita la contraseña'}),
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label='Rol en el sistema',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Usuario activo',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Ese nombre de usuario ya está registrado.')
        return username

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password != password_confirm:
            self.add_error('password_confirm', 'Las contraseñas no coinciden.')
        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error('password', exc)
        return cleaned


class SystemUserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label='Rol en el sistema',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        required=False,
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar en blanco para no cambiar',
        }),
    )
    password_confirm = forms.CharField(
        required=False,
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita la contraseña'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'Usuario',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Email',
            'is_active': 'Usuario activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        profile = getattr(self.instance, 'userprofile', None)
        if profile:
            self.fields['role'].initial = profile.role

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        exists = User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists()
        if exists:
            raise ValidationError('Ese nombre de usuario ya está registrado.')
        return username

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password or password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', 'Las contraseñas no coinciden.')
            else:
                try:
                    validate_password(password, user=self.instance)
                except ValidationError as exc:
                    self.add_error('password', exc)
        return cleaned
