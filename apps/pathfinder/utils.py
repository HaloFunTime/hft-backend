import json
import logging

from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.halo_infinite.utils import (
    SEASON_3_END_DAY,
    SEASON_3_END_TIME,
    SEASON_3_START_DAY,
    SEASON_3_START_TIME,
    get_343_recommended_file_contributors,
)
from apps.link.models import DiscordXboxLiveLink

logger = logging.getLogger(__name__)


def get_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        hike_attendances=Count(
            "pathfinder_hike_attendees",
            filter=Q(
                pathfinder_hike_attendees__attendee_discord_id__in=discord_ids,
                pathfinder_hike_attendees__attendance_date__range=[
                    SEASON_3_START_DAY,
                    SEASON_3_END_DAY,
                ],
            ),
        ),
        hike_submissions=Count(
            "pathfinder_hike_submitters",
            filter=Q(
                pathfinder_hike_submitters__map_submitter_discord_id__in=discord_ids,
                pathfinder_hike_submitters__scheduled_playtest_date__range=[
                    SEASON_3_START_DAY,
                    SEASON_3_END_DAY,
                ],
            ),
        ),
        waywo_posts=Count(
            "pathfinder_waywo_posters",
            filter=Q(
                pathfinder_waywo_posters__poster_discord_id__in=discord_ids,
                pathfinder_waywo_posters__created_at__range=[
                    SEASON_3_START_TIME,
                    SEASON_3_END_TIME,
                ],
            ),
        ),
    ).filter(discord_id__in=discord_ids)

    earn_dict = {}
    for account in annotated_discord_accounts:
        earn_dict[account.discord_id] = {
            "gone_hiking": min(account.hike_attendances, 5) * 50,  # Max 5 per account
            "map_maker": min(account.hike_submissions, 3) * 50,  # Max 3 per account
            "show_and_tell": min(account.waywo_posts, 2) * 50,  # Max 2 per account
        }
    return earn_dict


def get_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    earn_dict = {}
    for xuid in xuids:
        unlocked_bookmarked = False
        unlocked_playtime = False
        halofuntime_tags = 0
        forge_custom_game_hours = 0
        earn_dict[xuid] = {
            "bookmarked": 100 if unlocked_bookmarked else 0,
            "playtime": 100 if unlocked_playtime else 0,
            "tagtacular": min(halofuntime_tags, 4) * 25,
            "forged_in_fire": min(forge_custom_game_hours, 200),
        }

    return earn_dict


def get_illuminated_qualified(links: list[DiscordXboxLiveLink]) -> list[str]:
    illuminated_qualified_discord_ids = []
    xuid_to_discord_id = {
        link.xbox_live_account_id: link.discord_account_id for link in links
    }

    # Someone qualifies as Illuminated if their linked gamertag contributed to at least one file on 343's Recommended
    contributor_dict = get_343_recommended_file_contributors()
    illuminated_xuids = []
    for xuid in contributor_dict:
        # If the XUID from 343 recommended matches an XUID from one of our link records, they have qualified
        if xuid in xuid_to_discord_id:
            illuminated_xuids.append(xuid)

    illuminated_qualified_discord_ids = [
        xuid_to_discord_id[xuid] for xuid in illuminated_xuids
    ]
    return illuminated_qualified_discord_ids


def get_dynamo_qualified(
    discord_ids: list[str], links: list[DiscordXboxLiveLink]
) -> list[str]:
    points_by_discord_id = {discord_id: 0 for discord_id in discord_ids}

    # DISCORD CHALLENGES
    discord_earn_dict = get_discord_earn_dict(discord_ids)
    for discord_id in discord_earn_dict:
        discord_points = 0
        earns = discord_earn_dict.get(discord_id)

        # Gone Hiking
        discord_points += earns.get("gone_hiking")
        # Map Maker
        discord_points += earns.get("map_maker")
        # Show and Tell
        discord_points += earns.get("show_and_tell")

        points_by_discord_id[discord_id] = (
            points_by_discord_id[discord_id] + discord_points
        )

    # XBOX LIVE CHALLENGES
    xuids = [link.xbox_live_account_id for link in links]
    xuid_to_discord_id = {
        link.xbox_live_account_id: link.discord_account_id for link in links
    }

    xbox_earn_dict = get_xbox_earn_dict(xuids)
    for xuid in xbox_earn_dict:
        xbox_points = 0
        earns = xbox_earn_dict.get(xuid)

        # Bookmarked
        xbox_points += earns.get("bookmarked")
        # Playtime
        xbox_points += earns.get("playtime")
        # Tagtacular
        xbox_points += earns.get("tagtacular")
        # Forged in Fire
        xbox_points += earns.get("forged_in_fire")

        discord_id = xuid_to_discord_id.get(xuid)
        points_by_discord_id[discord_id] = (
            points_by_discord_id[discord_id] + xbox_points
        )

    logger.info("Pathfinder Dynamo point totals (by Discord ID):")
    logger.info(json.dumps(points_by_discord_id))

    dynamo_qualified_discord_ids = [
        k for k, v in points_by_discord_id.items() if v >= 500
    ]
    return dynamo_qualified_discord_ids
