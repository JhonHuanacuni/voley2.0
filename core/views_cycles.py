from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CycleForm
from .models import Cycle, Student
from .permissions import ensure_admin as _ensure_admin


@login_required(login_url='login')
def cycles_list(request):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    edit_cycle = None
    edit_id = request.GET.get('edit')

    if request.method == 'POST':
        form = CycleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cycles_list')
    elif edit_id:
        edit_cycle = get_object_or_404(Cycle, pk=edit_id)
        form = CycleForm(instance=edit_cycle)
    else:
        form = CycleForm()

    cycles = Cycle.objects.annotate(student_count=Count('students')).order_by('name')
    return render(request, 'core/cycles.html', {
        'cycles': cycles,
        'form': form,
        'create_mode': not edit_cycle,
        'edit_mode': bool(edit_cycle),
        'cycle': edit_cycle,
    })


@login_required(login_url='login')
def cycle_edit(request, cycle_id):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    cycle = get_object_or_404(Cycle, pk=cycle_id)

    if request.method == 'POST':
        form = CycleForm(request.POST, instance=cycle)
        if form.is_valid():
            form.save()
            return redirect('cycles_list')
        cycles = Cycle.objects.annotate(student_count=Count('students')).order_by('name')
        return render(request, 'core/cycles.html', {
            'cycles': cycles,
            'form': form,
            'cycle': cycle,
            'edit_mode': True,
        })

    return redirect(f"{reverse('cycles_list')}?edit={cycle_id}")


@login_required(login_url='login')
def cycle_delete(request, cycle_id):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    cycle = get_object_or_404(Cycle, pk=cycle_id)
    if request.method == 'POST':
        if Student.objects.filter(cycle=cycle).exists():
            return redirect('cycles_list')
        cycle.delete()
    return redirect('cycles_list')
