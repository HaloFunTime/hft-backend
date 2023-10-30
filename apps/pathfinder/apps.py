from django.apps import AppConfig


class PathfinderConfig(AppConfig):
    name = "apps.pathfinder"
    verbose_name = "Pathfinders"

    def ready(self):
        import apps.pathfinder.signals  # noqa
