from django.apps import AppConfig


class AppApiConfig(AppConfig):
    name = "plane.app"

    def ready(self):
        # Import signal handlers
        import plane.db.signals.velocity
