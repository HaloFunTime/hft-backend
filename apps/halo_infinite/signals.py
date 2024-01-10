import datetime
import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.halo_infinite.api.match import match_stats
from apps.halo_infinite.models import HaloInfiniteMatch, HaloInfinitePlaylist
from apps.halo_infinite.utils import get_playlist_latest_version_info

logger = logging.getLogger(__name__)


# NOTE: This method makes one Halo Infinite API call
@receiver(pre_save, sender=HaloInfiniteMatch)
def halo_infinite_match_pre_save(sender, instance, **kwargs):
    if not instance.data:
        data = match_stats(instance.match_id)
        instance.match_id = data.get("MatchId")
        instance.start_time = datetime.datetime.fromisoformat(
            data.get("MatchInfo", {}).get("StartTime")
        )
        instance.end_time = datetime.datetime.fromisoformat(
            data.get("MatchInfo", {}).get("EndTime")
        )
        instance.data = data


# NOTE: This method makes one Halo Infinite API call
@receiver(pre_save, sender=HaloInfinitePlaylist)
def halo_infinite_playlist_pre_save(sender, instance, **kwargs):
    latest_playlist_info = get_playlist_latest_version_info(instance.playlist_id)
    instance.playlist_id = latest_playlist_info.get("playlist_id")
    instance.version_id = latest_playlist_info.get("version_id")
    instance.ranked = latest_playlist_info.get("ranked")
    instance.name = latest_playlist_info.get("name")
    instance.description = latest_playlist_info.get("description")
