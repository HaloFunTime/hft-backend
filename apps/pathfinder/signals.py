import logging
import re

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.halo_infinite.api.match import match_stats
from apps.pathfinder.models import (
    PathfinderHikeGameParticipation,
    PathfinderHikeSubmission,
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PathfinderHikeSubmission)
def pathfinder_hike_submission_post_save(sender, instance, created, **kwargs):
    existing_game_participations = PathfinderHikeGameParticipation.objects.filter(
        hike_submission=instance
    )
    existing_xuids = {
        participation.xuid for participation in existing_game_participations
    }
    new_xuids = set()
    if instance.playtest_game_id is not None:
        # Get match info for the Halo Infinite match
        stats = match_stats(instance.playtest_game_id)
        players = stats.get("Players", [])
        for player in players:
            # Only award participation points to players present at match completion
            if player.get("ParticipationInfo", {}).get("PresentAtCompletion", False):
                xuid = int(re.search(r"\d+", player.get("PlayerId")).group())
                new_xuids.add(xuid)
    if existing_xuids != new_xuids:
        for participation in existing_game_participations:
            participation.delete()
        for xuid in new_xuids:
            PathfinderHikeGameParticipation.objects.create(
                hike_submission=instance, xuid=xuid, creator=instance.creator
            )
