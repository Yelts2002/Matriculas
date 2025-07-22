from django.apps import AppConfig

class MatriculasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'matriculas'

    def ready(self):
        import matriculas.signals  # Asegura que este archivo existe y se llama así
