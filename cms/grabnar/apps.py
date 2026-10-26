from django.apps import AppConfig


class GrabnarConfig(AppConfig):
    name = "grabnar"
    verbose_name = "Grabnar"

    def ready(self):
        from grabnar import signals  # noqa: F401
