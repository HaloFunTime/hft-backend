from django.apps import AppConfig


class Season04Config(AppConfig):
    name = "apps.season_04"
    verbose_name = "Season 4"

    def ready(self):
        import apps.season_04.signals  # noqa
