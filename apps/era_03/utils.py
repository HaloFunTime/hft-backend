import datetime
import logging
import random
from calendar import TUESDAY

import isodate
import pytz
import requests

from apps.era_03.models import (
    BoatAssignment,
    BoatDeckhand,
    BoatRank,
    WeeklyBoatAssignments,
)
from apps.halo_infinite.api.match import match_stats, matches_between
from apps.halo_infinite.constants import ERA_3_END_TIME, ERA_3_START_TIME, STATS
from apps.halo_infinite.models import HaloInfiniteMatch

EARLIEST_TIME = ERA_3_START_TIME
LATEST_TIME = ERA_3_END_TIME
TIER_ASSIGNMENT_CLASSIFICATIONS = {
    1: {BoatRank.Tracks.NA: [BoatAssignment.Classification.EASY]},
    2: {
        BoatRank.Tracks.NA: [
            BoatAssignment.Classification.EASY,
            BoatAssignment.Classification.EASY,
        ]
    },
    3: {
        BoatRank.Tracks.NA: [
            BoatAssignment.Classification.EASY,
            BoatAssignment.Classification.MEDIUM,
        ]
    },
    4: {
        BoatRank.Tracks.NA: [
            BoatAssignment.Classification.MEDIUM,
            BoatAssignment.Classification.MEDIUM,
        ]
    },
    # TODO: Add in Secrets of The Sea for promotions beyond tier 5
}


logger = logging.getLogger(__name__)


def get_current_week_start() -> datetime.date:
    # Figure out the current challenge week's start date
    now = datetime.datetime.now(pytz.timezone("America/Denver"))
    if now.weekday() == TUESDAY:
        if now.hour >= 11:
            # After cutoff time, today is the current week start date
            return now.date()
        else:
            # Before cutoff time, seven days ago is the current week start date
            return now.date() - datetime.timedelta(days=7)
    else:
        offset = (now.weekday() - TUESDAY) % 7
        return now.date() - datetime.timedelta(days=offset)


def get_next_rank(current_rank_tier: int, current_track: str) -> BoatRank:
    potential_next_ranks = BoatRank.objects.filter(tier=current_rank_tier + 1)
    if len(potential_next_ranks) == 0:
        raise Exception(
            f"No next rank found for tier {current_rank_tier} and track {current_track}."
        )
    elif len(potential_next_ranks) == 1:
        return potential_next_ranks.first()
    else:
        if current_track != BoatRank.Tracks.NA:
            # Pick a random promotion rank from the list of promotion ranks
            return random.choice(list(potential_next_ranks))
        else:
            # Pick the next rank on the track
            return potential_next_ranks.filter(
                tier=current_rank_tier + 1,
                track=current_track,
            ).first()


def check_xuid_assignment(
    xuid: int, assignment: BoatAssignment, current_week_start: datetime.date
) -> HaloInfiniteMatch | None:
    week_start_time = pytz.timezone("America/Denver").localize(
        datetime.datetime.combine(current_week_start, datetime.time(11, 0, 0))
    )
    week_end_time = pytz.timezone("America/Denver").localize(
        datetime.datetime.combine(
            current_week_start + datetime.timedelta(days=7), datetime.time(11, 0, 0)
        )
    )
    # Set match info to query against
    match_info_dict = {"LifecycleMode": 3}  # Challenges are matchmaking only
    if assignment.require_level_id is not None:
        match_info_dict["LevelId"] = str(assignment.require_level_id)
    if assignment.require_map_asset_id is not None:
        match_info_dict["MapVariant"] = {
            "AssetId": str(assignment.require_map_asset_id)
        }
    if assignment.require_mode_asset_id is not None:
        match_info_dict["UgcGameVariant"] = {
            "AssetId": str(assignment.require_mode_asset_id)
        }
    if assignment.require_playlist_asset_id is not None:
        match_info_dict["Playlist"] = {
            "AssetId": str(assignment.require_playlist_asset_id)
        }
    # Set player info to query against
    player_dict = {
        "PlayerId": f"xuid({xuid})",
    }
    if assignment.require_outcome:
        player_dict["Outcome"] = assignment.require_outcome
    hi_matches = HaloInfiniteMatch.objects.filter(
        start_time__gte=week_start_time,
        end_time__lt=week_end_time,
        data__MatchInfo__contains=match_info_dict,
        data__Players__contains=[player_dict],
    ).order_by("end_time")
    for hi_match in hi_matches:
        # Get the player data for each potential assignment-completing match
        player_data = None
        for player_dict in hi_match.data.get("Players", []):
            if player_dict.get("PlayerId") == f"xuid({xuid})":
                player_data = player_dict
                break
        # Check for assignment completion
        stat_path = assignment.stat.split("_")
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
                stat_data_type = STATS.get(assignment.stat)[0]
                actual_score = None
                assignment_score = None
                if stat_data_type == datetime.timedelta:
                    # Special case for durations
                    actual_score = isodate.parse_duration(str(data))
                    assignment_score = isodate.parse_duration(str(assignment.score))
                elif stat_data_type == list:
                    # Special case for medals
                    actual_score = 0
                    for medal in data:
                        if medal["NameId"] == assignment.medal_id:
                            actual_score = medal["Count"]
                            break
                    assignment_score = int(assignment.score)
                else:
                    # Should work for int and decimal.Decimal
                    actual_score = stat_data_type(data)
                    assignment_score = stat_data_type(assignment.score)
                if actual_score >= assignment_score:
                    logger.info(
                        f"Assignment {assignment} completed by xuid({xuid}) in match {hi_match.match_id}"
                    )
                    return hi_match
    return None


def fetch_match_ids_for_xuid(xuid: int, session: requests.Session = None) -> list[str]:
    matches = matches_between(
        xuid, EARLIEST_TIME, LATEST_TIME, session=session, ids_only=True
    )
    return [match.get("MatchId") for match in matches]


def generate_weekly_assignments(
    deckhand: BoatDeckhand, week_start: datetime.date, user: any
) -> WeeklyBoatAssignments:
    tier = deckhand.rank.tier
    track = deckhand.rank.track
    classifications = TIER_ASSIGNMENT_CLASSIFICATIONS.get(tier, {}).get(track, [])
    assignments = []
    for classification in classifications:
        assignments.append(
            BoatAssignment.objects.filter(classification=classification)
            .exclude(
                id__in=[assignment.id for assignment in assignments]
            )  # Avoid duplicate assignments
            .order_by("?")
            .first()
        )
    return WeeklyBoatAssignments.objects.create(
        deckhand=deckhand,
        week_start=week_start,
        assignment_1=assignments[0],
        assignment_2=assignments[1] if len(assignments) > 1 else None,
        assignment_3=assignments[2] if len(assignments) > 2 else None,
        next_rank=BoatRank.objects.filter(tier=tier + 1, track=track).first(),
        creator=user,
    )


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
