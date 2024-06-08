import datetime
import logging

import isodate
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.halo_infinite.api.files import get_map
from apps.halo_infinite.api.match import match_stats
from apps.halo_infinite.api.playlist import get_playlist, get_playlist_info
from apps.halo_infinite.models import (
    HaloInfiniteMap,
    HaloInfiniteMatch,
    HaloInfinitePlaylist,
)

logger = logging.getLogger(__name__)


# NOTE: This method makes one Halo Infinite API call
@receiver(pre_save, sender=HaloInfiniteMap)
def halo_infinite_map_pre_save(sender, instance, **kwargs):
    latest_map_data = get_map(instance.asset_id)
    if not latest_map_data:
        raise Exception(
            f"Map {instance.asset_id} is not published, so it cannot be saved."
        )
    instance.version_id = latest_map_data.get("VersionId")
    instance.public_name = latest_map_data.get("PublicName")
    instance.description = latest_map_data.get("Description")
    instance.published_at = isodate.parse_datetime(
        latest_map_data.get("PublishedDate", {}).get("ISO8601Date")
    )
    instance.data = latest_map_data


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


# NOTE: This method makes two Halo Infinite API calls
@receiver(pre_save, sender=HaloInfinitePlaylist)
def halo_infinite_playlist_pre_save(sender, instance, **kwargs):
    # Retrieve a requests session if one was bundled with the instance; otherwise create one
    requests_session = (
        getattr(instance, "requests_session")
        if hasattr(instance, "requests_session")
        else None
    )
    latest_playlist_info = get_playlist_info(instance.playlist_id, requests_session)
    instance.version_id = latest_playlist_info.get("UgcPlaylistVersion")
    instance.ranked = latest_playlist_info.get("HasCsr")
    instance.info = latest_playlist_info
    latest_playlist_data = get_playlist(
        instance.playlist_id, instance.version_id, requests_session
    )
    instance.name = latest_playlist_data.get("PublicName")
    instance.description = latest_playlist_data.get("Description")
    instance.data = latest_playlist_data
