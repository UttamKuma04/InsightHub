from django.apps import AppConfig


class ValidationServiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.validation_service"
    label = "validation_service"

    def ready(self):
        import apps.validation_service.receivers
