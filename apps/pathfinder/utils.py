import datetime
import logging

from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.halo_infinite.utils import (
    SEASON_3_DEV_MAP_IDS,
    SEASON_3_END_DAY,
    SEASON_3_END_TIME,
    SEASON_3_START_DAY,
    SEASON_3_START_TIME,
    get_343_recommended_contributors,
    get_authored_maps,
    get_season_3_custom_matches,
)

logger = logging.getLogger(__name__)


def get_s3_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        hike_attendances=Count(
            "pathfinder_hike_attendees",
            distinct=True,
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
            distinct=True,
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
            distinct=True,
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


def get_s3_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    earn_dict = {}
    for xuid in xuids:
        unlocked_bookmarked = False
        unlocked_playtime = False
        halofuntime_tags = 0
        forge_custom_game_hours = 0

        # Get maps authored by this XUID
        maps = get_authored_maps(xuid)

        # Get custom matches for this XUID
        custom_matches = get_season_3_custom_matches(xuid)
        custom_matches_sorted = sorted(
            custom_matches,
            key=lambda m: datetime.datetime.fromisoformat(
                m.get("MatchInfo", {}).get("StartTime")
            ),
        )

        # Bookmarked: Author a map that receives 100 or more bookmarks
        for map in maps:
            if map.get("Bookmarks", 0) >= 100:
                unlocked_bookmarked = True
                break

        # Playtime: Author a map that receives 500 or more plays
        for map in maps:
            if map.get("PlaysAllTime", 0) >= 500:
                unlocked_playtime = True
                break

        # Tagtacular: Tag authored maps with 'HaloFunTime'
        for map in maps:
            tags = map.get("Tags", [])
            if "halofuntime" in tags:
                halofuntime_tags += 1

        # Forged in Fire: Play 100+ hours of custom games on Forge maps
        custom_seconds_played = 0
        for match in custom_matches_sorted:
            # Only matches where the player was present count
            if (
                match.get("PresentAtEndOfMatch", False)
                and match.get("MatchInfo", {}).get("MapVariant", {}).get("AssetId", {})
                not in SEASON_3_DEV_MAP_IDS
            ):
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
            "bookmarked": 100 if unlocked_bookmarked else 0,
            "playtime": 100 if unlocked_playtime else 0,
            "tagtacular": min(halofuntime_tags, 4) * 25,
            "forged_in_fire": min(forge_custom_game_hours, 200),
        }

    return earn_dict


def is_illuminated_qualified(xuid: int) -> bool:
    # Someone qualifies as Illuminated if their linked gamertag contributed to:
    # - At least ONE map on 343's Recommended
    # - At least TWO modes on 343's Recommended
    # - At least TWO prefabs on 343's Recommended
    contributor_dict = get_343_recommended_contributors()
    map_qualified = False
    mode_qualified = False
    prefab_qualified = False
    if xuid in contributor_dict["map"]:
        map_qualified = True
    if xuid in contributor_dict["mode"] and contributor_dict["mode"][xuid] >= 2:
        mode_qualified = True
    if xuid in contributor_dict["prefab"] and contributor_dict["prefab"][xuid] >= 2:
        prefab_qualified = True
    return map_qualified or mode_qualified or prefab_qualified


def is_dynamo_qualified(discord_id: str, xuid: int | None) -> bool:
    points = 0

    # DISCORD CHALLENGES
    if discord_id is not None:
        discord_earn_dict = get_s3_discord_earn_dict([discord_id])
        earns = discord_earn_dict.get(discord_id)

        # Gone Hiking
        points += earns.get("gone_hiking")
        # Map Maker
        points += earns.get("map_maker")
        # Show and Tell
        points += earns.get("show_and_tell")

    # XBOX LIVE CHALLENGES
    if xuid is not None:
        xbox_earn_dict = get_s3_xbox_earn_dict([xuid])
        earns = xbox_earn_dict.get(xuid)

        # Bookmarked
        points += earns.get("bookmarked")
        # Playtime
        points += earns.get("playtime")
        # Tagtacular
        points += earns.get("tagtacular")
        # Forged in Fire
        points += earns.get("forged_in_fire")

    logger.info(f"Dynamo Points for {discord_id}: {points}")
    return points >= 500
