import datetime
import logging

import requests

from apps.halo_infinite.api.match import match_stats, matches_between
from apps.halo_infinite.constants import ERA_2_END_TIME, ERA_2_START_TIME
from apps.halo_infinite.models import HaloInfiniteMatch

logger = logging.getLogger(__name__)


def fetch_match_ids_for_xuid(xuid: int, session: requests.Session = None) -> list[str]:
    matches = matches_between(
        xuid, ERA_2_START_TIME, ERA_2_END_TIME, session=session, ids_only=True
    )
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
