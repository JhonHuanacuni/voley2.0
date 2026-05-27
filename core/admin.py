from django.contrib import admin
from .models import Attendance, Membership, Payment, Shift, Student, UserProfile


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('student', 'start_date', 'end_date', 'amount_due', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('student__name', 'student__dni')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'shift', 'enrollment_status', 'membership_start', 'membership_end', 'retired', 'monthly_fee')
    search_fields = ('name', 'contact', 'dni', 'email')
    list_filter = ('shift', 'enrollment_status', 'retired')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'start_time', 'end_time', 'active_days_display')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status')
    search_fields = ('student__name',)
    list_filter = ('status', 'date')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'membership', 'date', 'amount', 'method')
    search_fields = ('student__name',)
    list_filter = ('method', 'date')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')
