from django import forms
from django.forms import DateInput
from datetime import date
from .models import Attendance, Membership, Payment, Shift, Student
from .weekdays import WEEKDAY_CHOICES_MON_FIRST, WEEKDAY_ORDER_MON_FIRST, sort_weekdays


class StudentForm(forms.ModelForm):
    attendance_days = forms.MultipleChoiceField(
        choices=[(i, label) for i, label in enumerate(['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'])],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input form-check-input-lg'}),
        required=False,
        label='Días de asistencia',
    )

    # Override shift to include a placeholder first option and load dynamic turnos
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

    class Meta:
        model = Student
        fields = [
            'name',
            'age',
            'dni',
            'email',
            'contact',
            'guardian',
            'address',
            'shift',
            'birth_date',
            'enrollment_status',
            'monthly_fee',
            'enrollment_date',
            'membership_start',
            'membership_end',
            'attendance_days',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Edad'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'guardian': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del apoderado'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Dirección completa', 'rows': 1}),
            'shift': forms.Select(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'enrollment_status': forms.Select(attrs={'class': 'form-control'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cuota mensual'}),
            'enrollment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'attendance_days': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input form-check-input-lg'}),
        }

        labels = {
            'name': 'Nombre',
            'age': 'Edad',
            'dni': 'DNI',
            'email': 'Email',
            'contact': 'Teléfono',
            'guardian': 'Apoderado',
            'address': 'Dirección',
            'shift': 'Turno',
            'birth_date': 'Fecha de nacimiento',
            'enrollment_status': 'Estado de matrícula',
            'monthly_fee': 'Cuota mensual',
            'enrollment_date': 'Fecha de inscripción',
            'membership_start': 'Inicio de membresía',
            'membership_end': 'Fin de membresía',
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

    def clean_attendance_days(self):
        days = self.cleaned_data.get('attendance_days') or []
        if not days:
            return list(range(7))
        return [int(d) for d in days]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        is_new = not getattr(self.instance, 'pk', None)
        if is_new and not self.is_bound:
            self.fields['enrollment_date'].initial = date.today().isoformat()
            self.fields['membership_start'].initial = date.today().isoformat()

        if self.instance and self.instance.pk:
            for field_name in ('birth_date', 'enrollment_date', 'membership_start', 'membership_end'):
                value = getattr(self.instance, field_name, None)
                if value:
                    self.fields[field_name].initial = value.isoformat()

        self.fields['shift'].queryset = Shift.objects.order_by('name')


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
        choices=WEEKDAY_CHOICES_MON_FIRST,
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
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            if self.instance.pk and self.instance.active_days:
                self.fields['active_days'].initial = sort_weekdays(self.instance.active_days)
            else:
                self.fields['active_days'].initial = list(WEEKDAY_ORDER_MON_FIRST)

    def clean_active_days(self):
        days = self.cleaned_data.get('active_days') or []
        if not days:
            return list(WEEKDAY_ORDER_MON_FIRST)
        return sort_weekdays([int(d) for d in days])


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
