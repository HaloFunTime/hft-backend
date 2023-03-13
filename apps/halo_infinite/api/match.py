import datetime
import logging

import requests

from apps.halo_infinite.decorators import spartan_token

logger = logging.getLogger(__name__)


@spartan_token
def match_count(xuid: int, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    with requests.Session() as s:
        response = s.get(
            f"https://halostats.svc.halowaypoint.com/hi/players/xuid({xuid})/matches/count",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict


# TODO: Figure out why this endpoint doesn't seem to work
@spartan_token
def match_privacy(xuid: int, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    with requests.Session() as s:
        response = s.get(
            f"https://halostats.svc.halowaypoint.com/hi/players/xuid({xuid})/matches-privacy",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict


@spartan_token
def match_skill(xuid: int, match_id: str, **kwargs):
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    with requests.Session() as s:
        response = s.get(
            f"https://skill.svc.halowaypoint.com/hi/matches/{match_id}/skill?players=xuid({xuid})",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict


@spartan_token
def matches_between(
    xuid: int,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    type: str = None,
    **kwargs,
) -> list[dict]:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    match_list = []
    with requests.Session() as s:
        # Matches return in reverse chronological order, so retrieve matches until the start timestamp
        before_start_time = False
        start = 0
        while not before_start_time:
            query_string = f"?count=25&start={start}"
            if type is not None:
                query_string += f"&type={type}"
            # Grab matches in 25-match chunks
            response = s.get(
                f"https://halostats.svc.halowaypoint.com/hi/players/xuid({xuid})/matches{query_string}",
                headers=headers,
            )
            if response.status_code == 200:
                response_dict = response.json()
                # Break if no results were returned
                if len(response_dict.get("Results")) == 0:
                    break
                for match in response_dict.get("Results"):
                    if (
                        datetime.datetime.fromisoformat(
                            match.get("MatchInfo", {}).get("EndTime")
                        )
                        < start_time
                    ):
                        before_start_time = True
                    elif (
                        datetime.datetime.fromisoformat(
                            match.get("MatchInfo", {}).get("EndTime")
                        )
                        > end_time
                    ):
                        pass
                    else:
                        match_list.append(match)
                start = response_dict.get("Start") + 25
            else:
                break
    return match_list
