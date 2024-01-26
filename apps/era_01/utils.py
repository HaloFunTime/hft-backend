import datetime
import logging

import isodate
import requests

from apps.era_01.models import BingoChallenge
from apps.halo_infinite.api.match import match_stats, matches_between
from apps.halo_infinite.constants import ERA_1_END_TIME, ERA_1_START_TIME, STATS
from apps.halo_infinite.models import HaloInfiniteMatch

EARLIEST_TIME = ERA_1_START_TIME
LATEST_TIME = ERA_1_END_TIME

logger = logging.getLogger(__name__)


def fetch_match_ids_for_xuid(xuid: int, session: requests.Session = None) -> list[str]:
    matches = matches_between(xuid, EARLIEST_TIME, LATEST_TIME, session=session)
    return [match.get("MatchId") for match in matches]


def save_new_matches(match_ids: set[str], user) -> bool:
    try:
        with requests.Session() as s:
            for match_id in match_ids:
                data = match_stats(match_id, s)
                HaloInfiniteMatch.objects.create(
                    match_id=match_id,
                    start_time=datetime.datetime.fromisoformat(
                        data.get("MatchInfo", {}).get("StartTime")
                    ),
                    end_time=datetime.datetime.fromisoformat(
                        data.get("MatchInfo", {}).get("EndTime")
                    ),
                    data=data,
                    creator=user,
                )
        return True
    except Exception as ex:
        logger.error("Error attempting to save new matches.")
        logger.error(ex)
        return False


def check_xuid_challenge(
    xuid: int, challenge: BingoChallenge
) -> HaloInfiniteMatch | None:
    # Set match info to query against
    match_info_dict = {}
    if challenge.require_match_type is not None:
        match_info_dict["LifecycleMode"] = challenge.require_match_type
    if challenge.require_level_id is not None:
        match_info_dict["LevelId"] = str(challenge.require_level_id)
    if challenge.require_map_asset_id is not None:
        match_info_dict["MapVariant"] = {"AssetId": str(challenge.require_map_asset_id)}
    if challenge.require_mode_asset_id is not None:
        match_info_dict["UgcGameVariant"] = {
            "AssetId": str(challenge.require_mode_asset_id)
        }
    if challenge.require_playlist_asset_id is not None:
        match_info_dict["Playlist"] = {
            "AssetId": str(challenge.require_playlist_asset_id)
        }
    # Set player info to query against
    participation_info_dict = {}
    if challenge.require_present_at_beginning:
        participation_info_dict["PresentAtBeginning"] = True
    if challenge.require_present_at_completion:
        participation_info_dict["PresentAtCompletion"] = True
    player_dict = {
        "PlayerId": f"xuid({xuid})",
        "ParticipationInfo": participation_info_dict,
    }
    if challenge.require_outcome:
        player_dict["Outcome"] = challenge.require_outcome
    hi_matches = HaloInfiniteMatch.objects.filter(
        start_time__gte=EARLIEST_TIME,
        end_time__lte=LATEST_TIME,
        data__MatchInfo__contains=match_info_dict,
        data__Players__contains=[player_dict],
    ).order_by("end_time")
    for hi_match in hi_matches:
        # Get the player data for each potential challenge-completing match
        player_data = None
        for player_dict in hi_match.data.get("Players", []):
            if player_dict.get("PlayerId") == f"xuid({xuid})":
                player_data = player_dict
                break
        # Check for challenge completion
        stat_path = challenge.stat.split("_")
        for team_stats in player_data["PlayerTeamStats"]:
            data = team_stats.get("Stats")
            found = False
            while len(stat_path) > 0:
                stat_piece = stat_path.pop(0)
                if stat_piece in data:
                    data = data[stat_piece]
                    if len(stat_path) == 0:
                        found = True
                else:
                    break
            if found:
                stat_data_type = STATS.get(challenge.stat)[0]
                actual_score = None
                challenge_score = None
                if stat_data_type == datetime.timedelta:
                    # Special case for durations
                    actual_score = isodate.parse_duration(str(data))
                    challenge_score = isodate.parse_duration(str(challenge.score))
                elif stat_data_type == list:
                    # Special case for medals
                    actual_score = 0
                    for medal in data:
                        if medal["NameId"] == challenge.medal_id:
                            actual_score = medal["Count"]
                            break
                    challenge_score = int(challenge.score)
                else:
                    # Should work for int and decimal.Decimal
                    actual_score = stat_data_type(data)
                    challenge_score = stat_data_type(challenge.score)
                if actual_score >= challenge_score:
                    logger.info(
                        f"Challenge {challenge.id} completed by xuid({xuid}) in match {hi_match.match_id}"
                    )
                    return hi_match
    return None
