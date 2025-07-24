from django.apps import AppConfig
import sys

class MatriculasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'matriculas'

    def ready(self):
        if 'runserver' in sys.argv:
            from . import signals
