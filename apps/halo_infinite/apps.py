from django.apps import AppConfig


class HaloInfiniteConfig(AppConfig):
    name = "apps.halo_infinite"
    verbose_name = "Halo Infinite"

    def ready(self):
        import apps.halo_infinite.signals  # noqa
