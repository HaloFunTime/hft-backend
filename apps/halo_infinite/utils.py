import datetime
import logging

import requests

from apps.halo_infinite.api.career_rank import career_rank
from apps.halo_infinite.api.csr import get_csr
from apps.halo_infinite.api.files import get_map, get_mode
from apps.halo_infinite.api.map_mode_pair import get_map_mode_pair
from apps.halo_infinite.api.match import (
    last_25_matches,
    match_count,
    match_skill,
    matches_between,
)
from apps.halo_infinite.api.playlist import (
    get_playlist,
    playlist_info,
    playlist_version,
)
from apps.halo_infinite.api.recommended import recommended
from apps.halo_infinite.api.search import search_by_author
from apps.halo_infinite.api.service_record import service_record
from apps.halo_infinite.constants import (
    CAREER_RANKS,
    ERA_DATA_DICT,
    PLAYLIST_ID_RANKED_ARENA,
    SEARCH_ASSET_KIND_MAP,
    SEARCH_ASSET_KIND_MODE,
    SEARCH_ASSET_KIND_PREFAB,
    SEARCH_ASSET_KINDS,
    SEASON_DATA_DICT,
)
from apps.halo_infinite.exceptions import (
    MissingEraDataException,
    MissingSeasonDataException,
)
from apps.halo_infinite.models import HaloInfiniteMapModePair, HaloInfinitePlaylist

logger = logging.getLogger(__name__)


def get_api_ids_for_season(season_id):
    season_dict = SEASON_DATA_DICT.get(season_id, {})
    if "api_id" in season_dict:
        return [season_dict.get("api_id")]
    elif "api_ids" in season_dict:
        return season_dict.get("api_ids")
    raise Exception(f"Could not find API IDs for Season '{season_id}'")


def get_current_season_id() -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    for season_id in SEASON_DATA_DICT.keys():
        start_time, end_time = get_start_and_end_times_for_season(season_id)
        if start_time <= now < end_time:
            return season_id
    raise MissingSeasonDataException(f"Missing season ID for time '{now.isoformat()}'")


def get_current_era() -> int:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    for era in ERA_DATA_DICT.keys():
        start_time, end_time = get_start_and_end_times_for_era(era)
        if start_time <= now < end_time:
            return era
    raise MissingEraDataException(f"Missing era number for time '{now.isoformat()}'")


def get_dev_map_ids_for_season(season_id: str) -> str:
    """
    Returns a dict with keys representing all dev map file IDs for a season given a season ID.
    """
    dev_map_ids = SEASON_DATA_DICT.get(season_id, {}).get("dev_map_ids", None)
    if dev_map_ids is None:
        raise MissingSeasonDataException(
            f"Missing 'dev_map_ids' for Season with ID '{season_id}'"
        )
    return dev_map_ids


def get_first_and_last_days_for_season(
    season_id: str,
) -> tuple[datetime.date, datetime.date]:
    """
    Returns a tuple with the first and last days for a season given a season ID.
    """
    first_day = SEASON_DATA_DICT.get(season_id, {}).get("first_day", None)
    last_day = SEASON_DATA_DICT.get(season_id, {}).get("last_day", None)
    if first_day is None:
        raise MissingSeasonDataException(
            f"Missing 'first_day' for Season with ID '{season_id}'"
        )
    if last_day is None:
        raise MissingSeasonDataException(
            f"Missing 'last_day' for Season with ID '{season_id}'"
        )
    return first_day, last_day


def get_start_and_end_times_for_season(
    season_id: str,
) -> tuple[datetime.datetime, datetime.datetime]:
    """
    Returns a tuple with the start and end times for a season given a season ID.
    """
    start_time = SEASON_DATA_DICT.get(season_id, {}).get("start_time", None)
    end_time = SEASON_DATA_DICT.get(season_id, {}).get("end_time", None)
    if start_time is None:
        raise MissingSeasonDataException(
            f"Missing 'start_time' for Season with ID '{season_id}'"
        )
    if end_time is None:
        raise MissingSeasonDataException(
            f"Missing 'end_time' for Season with ID '{season_id}'"
        )
    return start_time, end_time


def get_ranked_arena_playlist_id_for_season(season_id: str) -> str:
    """
    Returns the Ranked Arena playlist ID for a season given a season ID.
    """
    playlist_id = SEASON_DATA_DICT.get(season_id, {}).get(
        "ranked_arena_playlist_id", None
    )
    if playlist_id is None:
        raise MissingSeasonDataException(
            f"Missing 'ranked_arena_playlist_id' for Season with ID '{season_id}'"
        )
    return playlist_id


def get_343_recommended_contributors() -> list[int, int]:
    """
    Returns a dict mapping XUIDs to the count of files they have currently featured in 343's Recommended File list.
    """
    contributors = {
        "map": {},
        "mode": {},
        "prefab": {},
    }
    recommended_data = recommended()
    for map in recommended_data.get("MapLinks"):
        for contributor in map.get("Contributors"):
            xuid = int(contributor.lstrip("xuid(").rstrip(")"))
            if xuid in contributors["map"]:
                contributors["map"][xuid] = contributors["map"][xuid] + 1
            else:
                contributors["map"][xuid] = 1
    for mode in recommended_data.get("UgcGameVariantLinks"):
        for contributor in mode.get("Contributors"):
            xuid = int(contributor.lstrip("xuid(").rstrip(")"))
            if xuid in contributors["mode"]:
                contributors["mode"][xuid] = contributors["mode"][xuid] + 1
            else:
                contributors["mode"][xuid] = 1
    for prefab in recommended_data.get("PrefabLinks"):
        for contributor in prefab.get("Contributors"):
            xuid = int(contributor.lstrip("xuid(").rstrip(")"))
            if xuid in contributors["prefab"]:
                contributors["prefab"][xuid] = contributors["prefab"][xuid] + 1
            else:
                contributors["prefab"][xuid] = 1
    return contributors


def get_active_ranked_playlists() -> list[HaloInfinitePlaylist]:
    playlists = HaloInfinitePlaylist.objects.filter(ranked=True, active=True).order_by(
        "name"
    )
    return playlists


def get_authored_maps(xuid: int) -> list[dict]:
    return [
        file
        for file in search_by_author(xuid)
        if file.get("AssetKind") == SEARCH_ASSET_KIND_MAP
    ]


def get_authored_modes(xuid: int) -> list[dict]:
    return [
        file
        for file in search_by_author(xuid)
        if file.get("AssetKind") == SEARCH_ASSET_KIND_MODE
    ]


def get_authored_prefabs(xuid: int) -> list[dict]:
    return [
        file
        for file in search_by_author(xuid)
        if file.get("AssetKind") == SEARCH_ASSET_KIND_PREFAB
    ]


def get_waypoint_file_url(file: dict) -> str | None:
    asset_kind = SEARCH_ASSET_KINDS.get(file.get("AssetKind"), 0)
    if asset_kind == "Map":
        return (
            f"https://www.halowaypoint.com/halo-infinite/ugc/maps/{file.get('AssetId')}"
        )
    elif asset_kind == "UgcGameVariant":
        return f"https://www.halowaypoint.com/halo-infinite/ugc/modes/{file.get('AssetId')}"
    elif asset_kind == "Prefab":
        return f"https://www.halowaypoint.com/halo-infinite/ugc/prefabs/{file.get('AssetId')}"
    return None


def get_career_ranks(xuids: list[int]):
    return_dict = {
        "career_ranks": {},
    }
    career_rank_data = career_rank(xuids)
    for reward_track in career_rank_data.get("RewardTracks"):
        xuid = int(reward_track.get("Id").lstrip("xuid(").rstrip(")"))
        rank_number = reward_track.get("Result").get("CurrentProgress").get("Rank")
        rank_score = (
            reward_track.get("Result").get("CurrentProgress").get("PartialProgress")
        )
        return_dict["career_ranks"][xuid] = {
            "current_rank_number": rank_number,
            "current_rank_name": CAREER_RANKS.get(rank_number).get("name"),
            "current_rank_score": rank_score,
            "current_rank_score_max": CAREER_RANKS.get(rank_number).get(
                "cumulative_score"
            )
            - CAREER_RANKS.get(rank_number - 1).get("cumulative_score"),
            "cumulative_score": CAREER_RANKS.get(rank_number - 1).get(
                "cumulative_score"
            )
            + rank_score,
            "cumulative_score_max": CAREER_RANKS.get(272).get("cumulative_score"),
        }
    return return_dict


def get_csr_after_match(xuid: int, match_id: str) -> int:
    skill = match_skill(xuid, match_id)
    try:
        return skill["Value"][0]["Result"]["RankRecap"]["PostMatchCsr"]["Value"]
    except Exception:
        return -1


def get_csrs(xuids: list[int], playlist_id: str):
    def get_tier_description(tier, subtier):
        return f"{tier}{f' {subtier}' if tier != 'Onyx' else ''}"

    return_dict = {
        "csrs": {},
    }
    csr_data = get_csr(xuids, playlist_id)
    for value in csr_data.get("Value"):
        xuid = int(value.get("Id").lstrip("xuid(").rstrip(")"))
        current = value.get("Result").get("Current")
        current_reset_max = value.get("Result").get("SeasonMax")
        all_time_max = value.get("Result").get("AllTimeMax")
        return_dict["csrs"][xuid] = {
            "current_csr": current.get("Value"),
            "current_tier": current.get("Tier"),
            "current_subtier": current.get("SubTier") + 1,
            "current_tier_description": get_tier_description(
                current.get("Tier"), current.get("SubTier") + 1
            ),
            "current_reset_max_csr": current_reset_max.get("Value"),
            "current_reset_max_tier": current_reset_max.get("Tier"),
            "current_reset_max_subtier": current_reset_max.get("SubTier") + 1,
            "current_reset_max_tier_description": get_tier_description(
                current_reset_max.get("Tier"), current_reset_max.get("SubTier") + 1
            ),
            "all_time_max_csr": all_time_max.get("Value"),
            "all_time_max_tier": all_time_max.get("Tier"),
            "all_time_max_subtier": all_time_max.get("SubTier") + 1,
            "all_time_max_tier_description": get_tier_description(
                all_time_max.get("Tier"), all_time_max.get("SubTier") + 1
            ),
        }
    return return_dict


def update_active_playlists() -> list[HaloInfinitePlaylist]:
    active_playlists = HaloInfinitePlaylist.objects.filter(active=True)
    with requests.Session() as s:
        for playlist in active_playlists:
            # Kinda hacky but by triggering the pre-save signal we hit the Halo API
            playlist.requests_session = s
            playlist.save()
    return active_playlists


def update_known_playlists():
    known_playlists = HaloInfinitePlaylist.objects.all()
    for playlist in known_playlists:
        # Kinda hacky but by triggering the pre-save signal we hit the Halo API
        playlist.save()


def get_contributor_xuids_for_maps_in_active_playlists() -> set[int]:
    contributor_xuids = set()
    # Retrieve MapModePair IDs (Asset/Version) for all active playlists
    active_playlists = HaloInfinitePlaylist.objects.filter(active=True)
    map_mode_pair_ids = set()
    for playlist in active_playlists:
        for rotation_entry in playlist.data.get("RotationEntries", []):
            map_mode_pair_ids.add(rotation_entry["AssetId"])

    # Retrieve contributor XUIDs for the MapLinks in each MapModePair
    for asset_id in map_mode_pair_ids:
        map_mode_pair = HaloInfiniteMapModePair.objects.get(asset_id=asset_id)
        for contributor in map_mode_pair.data.get("MapLink", {}).get("Contributors"):
            contributor_xuids.add(int(contributor.lstrip("xuid(").rstrip(")")))

    return contributor_xuids


def update_map_mode_pairs_for_playlists(
    playlists: list[HaloInfinitePlaylist],
    user,
) -> list[HaloInfiniteMapModePair]:
    map_mode_pairs = []
    with requests.Session() as s:
        # Retrieve MapModePair IDs (Asset/Version) for all active playlists
        map_mode_pair_ids = set()
        for playlist in playlists:
            for rotation_entry in playlist.data.get("RotationEntries", []):
                map_mode_pair_ids.add(
                    (rotation_entry["AssetId"], rotation_entry["VersionId"])
                )

        # Create or Update all relevant MapModePairs
        for map_mode_pair_id in map_mode_pair_ids:
            asset_id = map_mode_pair_id[0]
            version_id = map_mode_pair_id[1]
            map_mode_pair = get_map_mode_pair(asset_id, version_id, s)
            map_mode_pairs.append(
                HaloInfiniteMapModePair.objects.update_or_create(
                    asset_id=map_mode_pair.get("AssetId"),
                    defaults={
                        "version_id": map_mode_pair.get("VersionId"),
                        "public_name": map_mode_pair.get("PublicName"),
                        "description": map_mode_pair.get("Description"),
                        "data": map_mode_pair,
                        "creator": user,
                    },
                )
            )

    return map_mode_pairs


def get_playlist_latest_version_info(playlist_id: str):
    info_dict = playlist_info(playlist_id)
    version_dict = playlist_version(playlist_id, info_dict.get("UgcPlaylistVersion"))
    return {
        "playlist_id": version_dict.get("AssetId"),
        "version_id": version_dict.get("VersionId"),
        "ranked": info_dict.get("HasCsr"),
        "name": version_dict.get("PublicName"),
        "description": version_dict.get("Description"),
    }


def get_recent_games(xuid: int, match_type: str):
    last_10_games = last_25_matches(xuid, match_type)[:10]
    recent_games = []
    for game in last_10_games:
        match_id = game["MatchId"]
        map_asset_id = game["MatchInfo"]["MapVariant"]["AssetId"]
        map_version_id = game["MatchInfo"]["MapVariant"]["VersionId"]
        map_name = None
        map_thumbnail_url = None
        if map_asset_id is not None:
            map_data = get_map(map_asset_id, map_version_id)
            map_name = map_data["PublicName"]
            thumbnail_filepaths = list(
                filter(
                    lambda x: "thumbnail" in x,
                    map_data.get("Files", {}).get("FileRelativePaths", []),
                )
            )
            if len(thumbnail_filepaths) > 0:
                map_thumbnail_url = (
                    map_data.get("Files", {}).get("Prefix") + thumbnail_filepaths[0]
                )
        mode_asset_id = game["MatchInfo"]["UgcGameVariant"]["AssetId"]
        mode_version_id = game["MatchInfo"]["UgcGameVariant"]["VersionId"]
        mode_name = None
        if mode_asset_id is not None:
            mode_data = get_mode(mode_asset_id, mode_version_id)
            mode_name = mode_data["PublicName"]
        playlist_asset_id = None
        playlist_version_id = None
        playlist_name = None
        if game["MatchInfo"].get("Playlist", None) is not None:
            playlist_asset_id = game["MatchInfo"]["Playlist"]["AssetId"]
            playlist_version_id = game["MatchInfo"]["Playlist"]["VersionId"]
            playlist_data = get_playlist(playlist_asset_id, playlist_version_id)
            playlist_name = playlist_data["PublicName"]
        finished = game["PresentAtEndOfMatch"]
        outcome = (
            "Tied"
            if game["Outcome"] == 1
            else "Won"
            if game["Outcome"] == 2
            else "Lost"
        )
        recent_games.append(
            {
                "match_id": match_id,
                "outcome": outcome,
                "finished": finished,
                "mode_name": mode_name,
                "mode_asset_id": mode_asset_id,
                "mode_version_id": mode_version_id,
                "map_name": map_name,
                "map_asset_id": map_asset_id,
                "map_version_id": map_version_id,
                "map_thumbnail_url": map_thumbnail_url,
                "playlist_name": playlist_name,
                "playlist_asset_id": playlist_asset_id,
                "playlist_version_id": playlist_version_id,
            }
        )
    return recent_games


def get_season_custom_matches_for_xuid(xuid: int, season_id: str) -> list[dict]:
    start_time, end_time = get_start_and_end_times_for_season(season_id)
    return matches_between(xuid, start_time, end_time, "Custom")


def get_season_ranked_arena_matches_for_xuid(xuid: int, season_id: str) -> list[dict]:
    start_time, end_time = get_start_and_end_times_for_season(season_id)
    matches = matches_between(xuid, start_time, end_time, "Matchmaking")
    return [
        match
        for match in matches
        if match.get("MatchInfo", {}).get("Playlist", {}).get("AssetId")
        == get_ranked_arena_playlist_id_for_season(season_id)
    ]


def get_service_record_data(
    xuid: int, season_id: str | None, playlist_id: str | None
) -> dict:
    combined_service_record = {}
    season_api_ids = get_api_ids_for_season(season_id)
    for season_api_id in season_api_ids:
        combined_service_record[season_api_id] = service_record(
            xuid, season_api_id, playlist_id
        )
    return combined_service_record


def get_summary_stats(xuid: int):
    service_record_dict = service_record(xuid)
    match_count_dict = match_count(xuid)
    return {
        "matchmaking": {
            "games_played": match_count_dict.get("MatchmadeMatchesPlayedCount"),
            "wins": service_record_dict.get("Wins"),
            "losses": service_record_dict.get("Losses"),
            "ties": service_record_dict.get("Ties"),
            "kills": service_record_dict.get("CoreStats").get("Kills"),
            "deaths": service_record_dict.get("CoreStats").get("Deaths"),
            "assists": service_record_dict.get("CoreStats").get("Assists"),
            "kda": service_record_dict.get("CoreStats").get("AverageKDA"),
        },
        "custom": {
            "games_played": match_count_dict.get("CustomMatchesPlayedCount"),
        },
        "local": {"games_played": match_count_dict.get("LocalMatchesPlayedCount")},
        "games_played": match_count_dict.get("MatchesPlayedCount"),
    }


def get_start_and_end_times_for_era(
    era: int,
) -> tuple[datetime.datetime, datetime.datetime]:
    """
    Returns a tuple with the start and end times for an integer Era.
    """
    start_time = ERA_DATA_DICT.get(era, {}).get("start_time", None)
    end_time = ERA_DATA_DICT.get(era, {}).get("end_time", None)
    if start_time is None:
        raise MissingEraDataException(f"Missing 'start_time' for Era #{era}'")
    if end_time is None:
        raise MissingEraDataException(f"Missing 'end_time' for Era #{era}'")
    return start_time, end_time


def get_era_custom_matches_for_xuid(xuid: int, era: int) -> list[dict]:
    start_time, end_time = get_start_and_end_times_for_era(era)
    return matches_between(xuid, start_time, end_time, "Custom")


def get_era_ranked_arena_matches_for_xuid(xuid: int, era: int):
    start_time, end_time = get_start_and_end_times_for_era(era)
    matches = matches_between(xuid, start_time, end_time, "Matchmaking")
    return [
        match
        for match in matches
        if match.get("MatchInfo", {}).get("Playlist", {}).get("AssetId")
        == PLAYLIST_ID_RANKED_ARENA
    ]
