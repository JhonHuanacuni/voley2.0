WEEKDAY_LABELS = {
    0: 'Domingo',
    1: 'Lunes',
    2: 'Martes',
    3: 'Miércoles',
    4: 'Jueves',
    5: 'Viernes',
    6: 'Sábado',
}

WEEKDAY_CHOICES_MON_FIRST = [
    (1, 'Lunes'),
    (2, 'Martes'),
    (3, 'Miércoles'),
    (4, 'Jueves'),
    (5, 'Viernes'),
    (6, 'Sábado'),
    (0, 'Domingo'),
]

WEEKDAY_ORDER_MON_FIRST = [1, 2, 3, 4, 5, 6, 0]


def sort_weekdays(days):
    return sorted(days, key=lambda d: WEEKDAY_ORDER_MON_FIRST.index(d) if d in WEEKDAY_ORDER_MON_FIRST else 99)


def format_weekdays(days):
    if not days or len(days) == 7:
        return 'Todos'
    ordered = sort_weekdays(days)
    return ', '.join(WEEKDAY_LABELS[d] for d in ordered if d in WEEKDAY_LABELS)
