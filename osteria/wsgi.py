#server WSGI sito online
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osteria.settings')

application = get_wsgi_application()
