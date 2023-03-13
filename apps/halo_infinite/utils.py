import datetime
import logging

from apps.halo_infinite.api.csr import csr
from apps.halo_infinite.api.match import match_count, match_skill, matches_between
from apps.halo_infinite.api.playlist import playlist_info, playlist_version
from apps.halo_infinite.api.recommended import recommended
from apps.halo_infinite.api.service_record import service_record
from apps.halo_infinite.models import HaloInfinitePlaylist

logger = logging.getLogger(__name__)

SEASON_3_START_TIME = datetime.datetime.fromisoformat("2023-03-07T18:00:00Z")
SEASON_3_END_TIME = datetime.datetime.fromisoformat("2023-06-27T17:00:00Z")
SEASON_3_RANKED_ARENA_PLAYLIST_ID = "edfef3ac-9cbe-4fa2-b949-8f29deafd483"


def get_343_recommended_file_contributors() -> list[int, int]:
    """
    Returns a dict mapping XUIDs to the count of files they have currently featured in 343's Recommended File list.
    """
    contributors = {}
    recommended_data = recommended()
    for map in recommended_data.get("MapLinks"):
        for contributor in map.get("Contributors"):
            xuid = int(contributor.lstrip("xuid(").rstrip(")"))
            if xuid in contributors:
                contributors[xuid] = contributors[xuid] + 1
            else:
                contributors[xuid] = 1
    return contributors


def get_active_ranked_playlists() -> list[HaloInfinitePlaylist]:
    playlists = HaloInfinitePlaylist.objects.filter(ranked=True, active=True).order_by(
        "name"
    )
    return playlists


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
    csr_data = csr(xuids, playlist_id)
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


def get_season_3_ranked_arena_matches(xuid: int) -> list[dict]:
    season_3_matches = matches_between(
        xuid, SEASON_3_START_TIME, SEASON_3_END_TIME, "Matchmaking"
    )
    return [
        match
        for match in season_3_matches
        if match.get("MatchInfo", {}).get("Playlist", {}).get("AssetId")
        == SEASON_3_RANKED_ARENA_PLAYLIST_ID
    ]


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
