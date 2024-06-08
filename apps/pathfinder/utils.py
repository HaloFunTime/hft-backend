import datetime
import logging

from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.halo_infinite.constants import LEVEL_IDS_FORGE
from apps.halo_infinite.utils import (
    get_era_custom_matches_for_xuid,
    get_start_and_end_times_for_era,
)
from apps.pathfinder.models import PathfinderBeanCount, PathfinderHikeGameParticipation

logger = logging.getLogger(__name__)

BEAN_AWARD_HIKE_GAME_PARTICIPATION = 3
BEAN_AWARD_HIKE_VOICE_PARTICIPATION = 2
BEAN_AWARD_WAYWO_COMMENT = 1
BEAN_COST_HIKE_SUBMISSION = 50
PATHFINDER_WAYWO_COMMENT_MIN_LENGTH_FOR_BEAN_AWARD = 100


def change_beans(discord_account: DiscordAccount, bean_delta: int) -> bool:
    if check_beans(discord_account) + bean_delta >= 0:
        pbc = PathfinderBeanCount.objects.filter(
            bean_owner_discord=discord_account
        ).get()
        pbc.bean_count += bean_delta
        pbc.save()
        return True
    else:
        return False


def check_beans(discord_account: DiscordAccount) -> int:
    assert discord_account is not None
    try:
        pbc = PathfinderBeanCount.objects.filter(
            bean_owner_discord=discord_account
        ).get()
    except PathfinderBeanCount.DoesNotExist:
        pbc = PathfinderBeanCount.objects.create(
            bean_owner_discord=discord_account,
            bean_count=0,
            creator=discord_account.creator,
        )
    return pbc.bean_count


def get_e1_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    start_time, end_time = get_start_and_end_times_for_era(1)
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        hike_submissions=Count(
            "pathfinder_hike_submitters",
            distinct=True,
            filter=Q(
                pathfinder_hike_submitters__map_submitter_discord_id__in=discord_ids,
                pathfinder_hike_submitters__created_at__range=[
                    start_time,
                    end_time,
                ],
            ),
        ),
        waywo_posts=Count(
            "pathfinder_waywo_posters",
            distinct=True,
            filter=Q(
                pathfinder_waywo_posters__poster_discord_id__in=discord_ids,
                pathfinder_waywo_posters__created_at__range=[
                    start_time,
                    end_time,
                ],
            ),
        ),
        waywo_comments=Count(
            "pathfinder_waywo_commenters",
            distinct=True,
            filter=Q(
                pathfinder_waywo_commenters__commenter_discord_id__in=discord_ids,
                pathfinder_waywo_commenters__created_at__range=[
                    start_time,
                    end_time,
                ],
            ),
        ),
    ).filter(discord_id__in=discord_ids)

    earn_dict = {}
    for account in annotated_discord_accounts:
        earn_dict[account.discord_id] = {
            "bean_spender": min(account.hike_submissions, 1) * 200,  # Max 1 per account
            "what_are_you_working_on": min(account.waywo_posts, 3)
            * 50,  # Max 3 per account
            "feedback_fiend": min(account.waywo_comments, 100),  # Max 100 per account
        }
    return earn_dict


def get_e1_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    start_time, end_time = get_start_and_end_times_for_era(1)
    earn_dict = {}
    for xuid in xuids:
        # Get custom matches for this XUID
        custom_matches = get_era_custom_matches_for_xuid(xuid, 1)
        custom_matches_sorted = sorted(
            custom_matches,
            key=lambda m: datetime.datetime.fromisoformat(
                m.get("MatchInfo", {}).get("EndTime")
            ),
        )

        # Gone Hiking: Participate in Pathfinder Hikes playtesting in-game
        hike_game_participations = PathfinderHikeGameParticipation.objects.filter(
            xuid=xuid, created_at__range=[start_time, end_time]
        ).count()

        # Forged in Fire: Play hours of custom games on Forge maps
        custom_seconds_played = 0
        for match in custom_matches_sorted:
            if match.get("MatchInfo", {}).get("LevelId", {}) in LEVEL_IDS_FORGE:
                match_start = datetime.datetime.strptime(
                    match.get("MatchInfo", {})
                    .get("StartTime", None)
                    .rstrip("Z")
                    .split(".")[0],
                    "%Y-%m-%dT%H:%M:%S",
                ).replace(tzinfo=datetime.timezone.utc)
                match_end = datetime.datetime.strptime(
                    match.get("MatchInfo", {})
                    .get("EndTime", None)
                    .rstrip("Z")
                    .split(".")[0],
                    "%Y-%m-%dT%H:%M:%S",
                ).replace(tzinfo=datetime.timezone.utc)
                custom_seconds_played += (match_end - match_start).total_seconds()
        forge_custom_game_hours = int(custom_seconds_played / 3600)

        earn_dict[xuid] = {
            "gone_hiking": min(hike_game_participations, 25) * 10,  # Max 25 per account
            "forged_in_fire": min(forge_custom_game_hours, 200),
        }
    return earn_dict


def get_e2_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    start_time, end_time = get_start_and_end_times_for_era(2)
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        hike_submissions=Count(
            "pathfinder_hike_submitters",
            distinct=True,
            filter=Q(
                pathfinder_hike_submitters__map_submitter_discord_id__in=discord_ids,
                pathfinder_hike_submitters__created_at__range=[
                    start_time,
                    end_time,
                ],
            ),
        ),
        waywo_posts=Count(
            "pathfinder_waywo_posters",
            distinct=True,
            filter=Q(
                pathfinder_waywo_posters__poster_discord_id__in=discord_ids,
                pathfinder_waywo_posters__created_at__range=[
                    start_time,
                    end_time,
                ],
            ),
        ),
        waywo_comments=Count(
            "pathfinder_waywo_commenters",
            distinct=True,
            filter=Q(
                pathfinder_waywo_commenters__commenter_discord_id__in=discord_ids,
                pathfinder_waywo_commenters__created_at__range=[
                    start_time,
                    end_time,
                ],
            ),
        ),
    ).filter(discord_id__in=discord_ids)

    earn_dict = {}
    for account in annotated_discord_accounts:
        earn_dict[account.discord_id] = {
            "bean_spender": min(account.hike_submissions, 1) * 200,  # Max 1 per account
            "what_are_you_working_on": min(account.waywo_posts, 3)
            * 50,  # Max 3 per account
            "feedback_fiend": min(account.waywo_comments, 100),  # Max 100 per account
        }
    return earn_dict


def get_e2_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    start_time, end_time = get_start_and_end_times_for_era(2)
    earn_dict = {}
    for xuid in xuids:
        # Get custom matches for this XUID
        custom_matches = get_era_custom_matches_for_xuid(xuid, 2)
        custom_matches_sorted = sorted(
            custom_matches,
            key=lambda m: datetime.datetime.fromisoformat(
                m.get("MatchInfo", {}).get("EndTime")
            ),
        )

        # Gone Hiking: Participate in Pathfinder Hikes playtesting in-game
        hike_game_participations = PathfinderHikeGameParticipation.objects.filter(
            xuid=xuid, created_at__range=[start_time, end_time]
        ).count()

        # Forged in Fire: Play hours of custom games on Forge maps
        custom_seconds_played = 0
        for match in custom_matches_sorted:
            if match.get("MatchInfo", {}).get("LevelId", {}) in LEVEL_IDS_FORGE:
                match_start = datetime.datetime.strptime(
                    match.get("MatchInfo", {})
                    .get("StartTime", None)
                    .rstrip("Z")
                    .split(".")[0],
                    "%Y-%m-%dT%H:%M:%S",
                ).replace(tzinfo=datetime.timezone.utc)
                match_end = datetime.datetime.strptime(
                    match.get("MatchInfo", {})
                    .get("EndTime", None)
                    .rstrip("Z")
                    .split(".")[0],
                    "%Y-%m-%dT%H:%M:%S",
                ).replace(tzinfo=datetime.timezone.utc)
                custom_seconds_played += (match_end - match_start).total_seconds()
        forge_custom_game_hours = int(custom_seconds_played / 3600)

        earn_dict[xuid] = {
            "gone_hiking": min(hike_game_participations, 25) * 10,  # Max 25 per account
            "forged_in_fire": min(forge_custom_game_hours, 200),
        }
    return earn_dict
