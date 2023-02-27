import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.halo_infinite.models import HaloInfinitePlaylist
from apps.halo_infinite.utils import get_playlist_latest_version_info

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=HaloInfinitePlaylist)
def halo_infinite_playlist_pre_save(sender, instance, **kwargs):
    latest_playlist_info = get_playlist_latest_version_info(instance.playlist_id)
    instance.playlist_id = latest_playlist_info.get("playlist_id")
    instance.version_id = latest_playlist_info.get("version_id")
    instance.ranked = latest_playlist_info.get("ranked")
    instance.name = latest_playlist_info.get("name")
    instance.description = latest_playlist_info.get("description")
