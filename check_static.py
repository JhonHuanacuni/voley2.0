from pathlib import Path
from django.conf import settings
from django.contrib.staticfiles import finders

BASE_DIR = Path('d:/voley2.0')
settings.configure(
    BASE_DIR=BASE_DIR,
    INSTALLED_APPS=['django.contrib.staticfiles'],
    STATIC_URL='/static/',
    STATICFILES_DIRS=[BASE_DIR / 'core' / 'static'],
)
print('css exists', (BASE_DIR / 'core' / 'static' / 'css' / 'sb-admin-2.min.css').exists())
print('js exists', (BASE_DIR / 'core' / 'static' / 'js' / 'sb-admin-2.min.js').exists())
print('find css', finders.find('css/sb-admin-2.min.css'))
print('find js', finders.find('js/sb-admin-2.min.js'))
