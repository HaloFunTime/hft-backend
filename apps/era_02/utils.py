import datetime
import logging
import re

import isodate
import requests

from apps.era_02.models import TeamUpChallengeCompletion, TeamUpChallenges
from apps.halo_infinite.api.match import match_stats, matches_between
from apps.halo_infinite.constants import (
    ERA_2_END_TIME,
    ERA_2_START_TIME,
    GAME_VARIANT_CATEGORY_FIREFIGHT,
    MEDAL_ID_360,
    MEDAL_ID_DEMON,
    MEDAL_ID_IMMORTAL_CHAUFFEUR,
    MEDAL_ID_STICK,
)
from apps.halo_infinite.models import HaloInfiniteMatch

logger = logging.getLogger(__name__)


def fetch_match_ids_for_xuid(xuid: int, session: requests.Session = None) -> list[str]:
    matches = matches_between(
        xuid,
        ERA_2_START_TIME,
        ERA_2_END_TIME,
        type="Matchmaking",
        session=session,
        ids_only=True,
    )
    return [match.get("MatchId") for match in matches]


def save_challenge_completions_for_match(match: HaloInfiniteMatch, user) -> None:
    # Early exit if no teams
    if not match.data.get("Teams"):
        return

    # Early exit if custom game
    if not match.data.get("MatchInfo", {}).get("Playlist"):
        return

    # Early exit if the game mode is disallowed
    if match.data.get("MatchInfo", {}).get("GameVariantCategory") in {
        GAME_VARIANT_CATEGORY_FIREFIGHT
    }:
        return

    # Evaluate the stats from the winning team to see if the players completed any challenges
    top_teams = [t for t in match.data["Teams"] if t["Rank"] == 1]
    winning_teams = [t for t in top_teams if t["Outcome"] == 2]
    winning_team = winning_teams[0] if winning_teams else None
    if winning_team is None:
        return
    winning_team_stats = winning_team["Stats"]
    winning_team_medals = winning_team_stats["CoreStats"]["Medals"]
    completed_challenges = []
    for challenge in [c[0] for c in TeamUpChallenges.choices]:
        score = None
        match challenge:
            case TeamUpChallenges.BAIT_THE_FLAGS:
                if (
                    "CaptureTheFlagStats" in winning_team_stats
                    and winning_team_stats["CaptureTheFlagStats"]["FlagReturnersKilled"]
                    >= 10
                ):
                    score = str(
                        winning_team_stats["CaptureTheFlagStats"]["FlagReturnersKilled"]
                    )
            case TeamUpChallenges.FORTY_FISTS:
                if winning_team_stats["CoreStats"]["MeleeKills"] >= 40:
                    score = str(winning_team_stats["CoreStats"]["MeleeKills"])
            case TeamUpChallenges.GRENADE_PARADE:
                if winning_team_stats["CoreStats"]["GrenadeKills"] >= 25:
                    score = str(winning_team_stats["CoreStats"]["GrenadeKills"])
            case TeamUpChallenges.HUNDRED_HEADS:
                if winning_team_stats["CoreStats"]["HeadshotKills"] >= 100:
                    score = str(winning_team_stats["CoreStats"]["HeadshotKills"])
            case TeamUpChallenges.MOST_VALUABLE_DRIVER:
                medal_dicts = [
                    medal
                    for medal in winning_team_medals
                    if medal["NameId"] == MEDAL_ID_IMMORTAL_CHAUFFEUR
                ]
                medal_dict = medal_dicts[0] if medal_dicts else {}
                if medal_dict.get("Count", 0) >= 1:
                    score = str(medal_dict.get("Count", 0))
            case TeamUpChallenges.OWN_THE_ZONES:
                if "ZonesStats" in winning_team_stats and isodate.parse_duration(
                    winning_team_stats["ZonesStats"]["StrongholdOccupationTime"]
                ) >= isodate.parse_duration("PT25M"):
                    score = str(
                        winning_team_stats["ZonesStats"]["StrongholdOccupationTime"]
                    )
            case TeamUpChallenges.SPEED_FOR_SEEDS:
                if "StockpileStats" in winning_team_stats and isodate.parse_duration(
                    winning_team_stats["StockpileStats"]["TimeAsPowerSeedDriver"]
                ) >= isodate.parse_duration("PT10M"):
                    score = str(
                        winning_team_stats["StockpileStats"]["TimeAsPowerSeedDriver"]
                    )
            case TeamUpChallenges.SPIN_CLASS:
                medal_dicts = [
                    medal
                    for medal in winning_team_medals
                    if medal["NameId"] == MEDAL_ID_360
                ]
                medal_dict = medal_dicts[0] if medal_dicts else {}
                if medal_dict.get("Count", 0) >= 10:
                    score = str(medal_dict.get("Count", 0))
            case TeamUpChallenges.STICKY_ICKY:
                medal_dicts = [
                    medal
                    for medal in winning_team_medals
                    if medal["NameId"] == MEDAL_ID_STICK
                ]
                medal_dict = medal_dicts[0] if medal_dicts else {}
                if medal_dict.get("Count", 0) >= 10:
                    score = str(medal_dict.get("Count", 0))
            case TeamUpChallenges.SUMMON_A_DEMON:
                medal_dicts = [
                    medal
                    for medal in winning_team_medals
                    if medal["NameId"] == MEDAL_ID_DEMON
                ]
                medal_dict = medal_dicts[0] if medal_dicts else {}
                if medal_dict.get("Count", 0) >= 1:
                    score = str(medal_dict.get("Count", 0))
        if score:
            completed_challenges.append((challenge, score))

    # Create TeamUpChallengeCompletion records for each XUID/completed challenge pair
    winning_team_players = [
        player
        for player in match.data["Players"]
        if player.get("LastTeamId") == winning_team["TeamId"]
    ]
    winning_team_xuids = [
        int(re.search(r"\d+", player.get("PlayerId")).group())
        for player in winning_team_players
    ]
    for challenge, score in completed_challenges:
        for xuid in winning_team_xuids:
            TeamUpChallengeCompletion.objects.create(
                match=match,
                challenge=challenge,
                xuid=xuid,
                score=score,
                creator=user,
            )


def save_new_matches(match_ids: set[str], user) -> bool:
    try:
        with requests.Session() as s:
            for match_id in match_ids:
                data = match_stats(match_id, s)
                match = HaloInfiniteMatch.objects.create(
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
                save_challenge_completions_for_match(match, user)
        return True
    except Exception as ex:
        logger.error("Error attempting to save new matches.")
        logger.error(ex)
        return False
