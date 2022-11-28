from django.apps import AppConfig


class XboxLiveConfig(AppConfig):
    name = "apps.xbox_live"
    verbose_name = "Xbox Live"

    def ready(self):
        import apps.xbox_live.signals  # noqa
