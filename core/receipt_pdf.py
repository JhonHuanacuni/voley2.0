from io import BytesIO
from pathlib import Path

from django.conf import settings
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import white
from reportlab.pdfgen import canvas

TEMPLATE_PATH = (
    Path(settings.BASE_DIR)
    / 'core'
    / 'static'
    / 'template Boleta'
    / 'plantilla Voley Vita.pdf'
)

PAGE_WIDTH = 595.56
PAGE_HEIGHT = 842.04
FONT_SIZE = 12
# Distancia entre el texto y la línea inferior (igual que CLIENTE / TELÉFONO).
TEXT_ABOVE_LINE = 14

# Posiciones medidas desde la plantilla (coordenada top de pdfplumber).
FIELD_POSITIONS = {
    'sale_number': (465, 80),
    'date_day': (451, 128),
    'date_month': (481, 128),
    'date_year': (521, 128),
    'client': (105, 184),
    'dni': (465, 184),
    'address': (115, 214),
    'email': (90, 243),
    'phone': (460, 243),
    'description': (70, 384),
    'amount': (500, 384),
    'total': (500, 574),
}

# Campos con subrayado en plantilla: line_top = fila de la línea ________.
UNDERLINE_FIELDS = {
    'shift': {'text_x': 92, 'line_top': 289},
    'payment_method': {'text_x': 154, 'line_top': 320},
}


def _baseline(top: float, offset: float = 12) -> float:
    return PAGE_HEIGHT - top - offset


def _draw_text(c, text, x, top, size=FONT_SIZE, align='left'):
    if not text:
        return
    text = str(text).upper()
    c.setFont('Helvetica', size)
    y = _baseline(top, offset=size)
    if align == 'right':
        c.drawRightString(x, y, text)
    elif align == 'center':
        c.drawCentredString(x, y, text)
    else:
        c.drawString(x, y, text)


def _draw_text_above_underline(c, text, text_x, line_top, size=FONT_SIZE):
    """Escribe el valor encima de la línea ________ sin borrarla."""
    if not text:
        return
    text = str(text).upper()
    text_top = line_top - TEXT_ABOVE_LINE
    c.setFont('Helvetica', size)
    c.drawString(text_x, _baseline(text_top, offset=size), text)


def _cover_placeholder(c, x, top, width, height):
    c.setFillColor(white)
    c.rect(x, _baseline(top) - 2, width, height, stroke=0, fill=1)
    c.setFillColor('black')


def fill_payment_receipt(payment, student, month_name):
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f'No se encontró la plantilla PDF: {TEMPLATE_PATH}')

    amount = f'S/ {payment.amount:.2f}'
    description = f'Cuota mensual - {month_name} {payment.date.year}'
    sale_number = str(payment.id).zfill(6)
    day = payment.date.strftime('%d')
    month = payment.date.strftime('%m')
    year = payment.date.strftime('%Y')

    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    _cover_placeholder(c, 458, 178, 35, 14)
    _draw_text(c, f'N° {sale_number}', *FIELD_POSITIONS['sale_number'])
    _draw_text(c, day, *FIELD_POSITIONS['date_day'], align='center')
    _draw_text(c, month, *FIELD_POSITIONS['date_month'], align='center')
    _draw_text(c, year, *FIELD_POSITIONS['date_year'], align='center')
    _draw_text(c, student.name or '', *FIELD_POSITIONS['client'])
    _draw_text(c, student.dni or '', *FIELD_POSITIONS['dni'])
    _draw_text(c, student.address or '', *FIELD_POSITIONS['address'])
    _draw_text(c, student.email or '', *FIELD_POSITIONS['email'])
    _draw_text(c, student.contact or '', *FIELD_POSITIONS['phone'])
    shift_field = UNDERLINE_FIELDS['shift']
    _draw_text_above_underline(
        c,
        student.get_shift_display() or '',
        shift_field['text_x'],
        shift_field['line_top'],
    )
    method_field = UNDERLINE_FIELDS['payment_method']
    _draw_text_above_underline(
        c,
        payment.get_method_display() or '',
        method_field['text_x'],
        method_field['line_top'],
    )
    _draw_text(c, description, *FIELD_POSITIONS['description'])
    _draw_text(c, amount, *FIELD_POSITIONS['amount'], align='right')
    _draw_text(c, amount, *FIELD_POSITIONS['total'], align='right')

    c.save()
    packet.seek(0)

    reader = PdfReader(str(TEMPLATE_PATH))
    page = reader.pages[0]
    page.merge_page(PdfReader(packet).pages[0])

    output = BytesIO()
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(output)
    output.seek(0)
    return output
