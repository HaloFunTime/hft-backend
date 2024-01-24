import datetime
import logging

from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.halo_infinite.api.files import get_map, get_mode, get_prefab
from apps.halo_infinite.constants import LEVEL_IDS_FORGE
from apps.halo_infinite.utils import (
    get_343_recommended_contributors,
    get_authored_maps,
    get_current_season_id,
    get_dev_map_ids_for_season,
    get_era_custom_matches_for_xuid,
    get_first_and_last_days_for_season,
    get_season_custom_matches_for_xuid,
    get_start_and_end_times_for_era,
    get_start_and_end_times_for_season,
)
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.models import PathfinderBeanCount, PathfinderHikeGameParticipation
from apps.showcase.models import ShowcaseFile

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


def get_s3_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    first_day, last_day = get_first_and_last_days_for_season("3")
    start_time, end_time = get_start_and_end_times_for_season("3")
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        hike_attendances=Count(
            "pathfinder_hike_attendees",
            distinct=True,
            filter=Q(
                pathfinder_hike_attendees__attendee_discord_id__in=discord_ids,
                pathfinder_hike_attendees__attendance_date__range=[
                    first_day,
                    last_day,
                ],
            ),
        ),
        hike_submissions=Count(
            "pathfinder_hike_submitters",
            distinct=True,
            filter=Q(
                pathfinder_hike_submitters__map_submitter_discord_id__in=discord_ids,
                pathfinder_hike_submitters__scheduled_playtest_date__range=[
                    first_day,
                    last_day,
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
    dev_map_ids = get_dev_map_ids_for_season("3")
    earn_dict = {}
    for xuid in xuids:
        unlocked_bookmarked = False
        unlocked_playtime = False
        halofuntime_tags = 0
        forge_custom_game_hours = 0

        # Get maps authored by this XUID
        maps = get_authored_maps(xuid)

        # Get custom matches for this XUID
        custom_matches = get_season_custom_matches_for_xuid(xuid, "3")
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
                not in dev_map_ids
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


def is_s3_dynamo_qualified(discord_id: str, xuid: int | None) -> bool:
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


def get_s4_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    first_day, last_day = get_first_and_last_days_for_season("4")
    start_time, end_time = get_start_and_end_times_for_season("4")
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        hike_attendances=Count(
            "pathfinder_hike_attendees",
            distinct=True,
            filter=Q(
                pathfinder_hike_attendees__attendee_discord_id__in=discord_ids,
                pathfinder_hike_attendees__attendance_date__range=[
                    first_day,
                    last_day,
                ],
            ),
        ),
        hike_submissions=Count(
            "pathfinder_hike_submitters",
            distinct=True,
            filter=Q(
                pathfinder_hike_submitters__map_submitter_discord_id__in=discord_ids,
                pathfinder_hike_submitters__scheduled_playtest_date__range=[
                    first_day,
                    last_day,
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
        testing_lfg_posts=Count(
            "pathfinder_testing_lfg_posters",
            distinct=True,
            filter=Q(
                pathfinder_testing_lfg_posters__poster_discord_id__in=discord_ids,
                pathfinder_testing_lfg_posters__created_at__range=[
                    start_time,
                    end_time,
                ],
            ),
        ),
    ).filter(discord_id__in=discord_ids)

    earn_dict = {}
    for account in annotated_discord_accounts:
        earn_dict[account.discord_id] = {
            "gone_hiking": min(account.hike_attendances, 5) * 50,  # Max 5 per account
            "the_road_more_traveled": min(account.hike_submissions, 2)
            * 50,  # Max 2 per account
            "block_talk": min(account.waywo_posts, 2) * 25,  # Max 2 per account
            "test_driven": min(account.testing_lfg_posts, 2) * 50,  # Max 2 per account
        }
    return earn_dict


def get_s4_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    dev_map_ids = get_dev_map_ids_for_season("4")
    earn_dict = {}
    for xuid in xuids:
        link = DiscordXboxLiveLink.objects.get(xbox_live_account_id=xuid)

        # Get custom matches for this XUID
        custom_matches = get_season_custom_matches_for_xuid(xuid, "4")
        custom_matches_sorted = sorted(
            custom_matches,
            key=lambda m: datetime.datetime.fromisoformat(
                m.get("MatchInfo", {}).get("StartTime")
            ),
        )

        # Showing Off: Add files to your Showcase
        showcase_files = ShowcaseFile.objects.filter(
            showcase_owner_id=link.discord_account_id
        )

        # Play On: Accumulate plays on maps and modes in your Showcase
        showcase_file_plays = 0
        for file in showcase_files:
            if file.file_type == ShowcaseFile.FileType.Map:
                file_data = get_map(file.file_id)
            if file.file_type == ShowcaseFile.FileType.Mode:
                file_data = get_mode(file.file_id)
            elif file.file_type == ShowcaseFile.FileType.Prefab:
                file_data = get_prefab(file.file_id)
            showcase_file_plays += file_data.get("AssetStats", {}).get(
                "PlaysAllTime", 0
            )

        # Forged in Fire: Play hours of custom games on Forge maps
        custom_seconds_played = 0
        for match in custom_matches_sorted:
            # Only matches where the player was present count
            if (
                match.get("PresentAtEndOfMatch", False)
                and match.get("MatchInfo", {}).get("MapVariant", {}).get("AssetId", {})
                not in dev_map_ids
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
            "showing_off": min(len(showcase_files), 3) * 50,
            "play_on": int(min(showcase_file_plays, 1500) / 10),
            "forged_in_fire": min(forge_custom_game_hours, 200),
        }
    return earn_dict


def is_s4_dynamo_qualified(discord_id: str, xuid: int | None) -> bool:
    points = 0

    # DISCORD CHALLENGES
    if discord_id is not None:
        discord_earn_dict = get_s4_discord_earn_dict([discord_id])
        earns = discord_earn_dict.get(discord_id)

        # Gone Hiking
        points += earns.get("gone_hiking")
        # The Road More Traveled
        points += earns.get("the_road_more_traveled")
        # Block Talk
        points += earns.get("block_talk")
        # Test Driven
        points += earns.get("test_driven")

    # XBOX LIVE CHALLENGES
    if xuid is not None:
        xbox_earn_dict = get_s4_xbox_earn_dict([xuid])
        earns = xbox_earn_dict.get(xuid)

        # Showing Off
        points += earns.get("showing_off")
        # Play On
        points += earns.get("play_on")
        # Forged in Fire
        points += earns.get("forged_in_fire")

    logger.info(f"Dynamo Points for {discord_id}: {points}")
    return points >= 500


def get_s5_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    start_time, end_time = get_start_and_end_times_for_season("5")
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


def get_s5_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    dev_map_ids = get_dev_map_ids_for_season("5")
    start_time, end_time = get_start_and_end_times_for_season("5")
    earn_dict = {}
    for xuid in xuids:
        # Get custom matches for this XUID
        custom_matches = get_season_custom_matches_for_xuid(xuid, "5")
        custom_matches_sorted = sorted(
            custom_matches,
            key=lambda m: datetime.datetime.fromisoformat(
                m.get("MatchInfo", {}).get("StartTime")
            ),
        )

        # Gone Hiking: Participate in Pathfinder Hikes playtesting in-game
        hike_game_participations = PathfinderHikeGameParticipation.objects.filter(
            xuid=xuid, created_at__range=[start_time, end_time]
        ).count()

        # Forged in Fire: Play hours of custom games on Forge maps
        custom_seconds_played = 0
        for match in custom_matches_sorted:
            if (
                match.get("MatchInfo", {}).get("MapVariant", {}).get("AssetId", {})
                not in dev_map_ids
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
            "gone_hiking": min(hike_game_participations, 25) * 10,  # Max 25 per account
            "forged_in_fire": min(forge_custom_game_hours, 200),
        }
    return earn_dict


def is_s5_dynamo_qualified(discord_id: str, xuid: int | None) -> bool:
    points = 0

    # DISCORD CHALLENGES
    if discord_id is not None:
        discord_earn_dict = get_s5_discord_earn_dict([discord_id])
        earns = discord_earn_dict.get(discord_id)

        # Bean Spender
        points += earns.get("bean_spender")
        # What Are You Working On?
        points += earns.get("what_are_you_working_on")
        # Feedback Fiend
        points += earns.get("feedback_fiend")

    # XBOX LIVE CHALLENGES
    if xuid is not None:
        xbox_earn_dict = get_s5_xbox_earn_dict([xuid])
        earns = xbox_earn_dict.get(xuid)

        # Gone Hiking
        points += earns.get("gone_hiking")
        # Forged in Fire
        points += earns.get("forged_in_fire")

    logger.info(f"Dynamo Points for {discord_id}: {points}")
    return points >= 500


def is_dynamo_qualified(discord_id: str, xuid: int | None) -> bool:
    season_id = get_current_season_id()
    if season_id == "3":
        return is_s3_dynamo_qualified(discord_id, xuid)
    elif season_id == "4":
        return is_s4_dynamo_qualified(discord_id, xuid)
    elif season_id == "5":
        return is_s5_dynamo_qualified(discord_id, xuid)
    return False


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
