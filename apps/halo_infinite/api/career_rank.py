import logging
import math

import requests

from apps.halo_infinite.decorators import clearance_token, spartan_token

logger = logging.getLogger(__name__)


@clearance_token
@spartan_token
def career_rank(xuids: list[int], **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    clearance_token = kwargs.get("HaloInfiniteClearanceToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
        "343-clearance": clearance_token.flight_configuration_id,
    }
    # Build XUID strings for every 30 XUIDs, as that is the max allowed per API call
    xuid_strings = []
    for i in range(math.ceil(len(xuids) / 30)):
        start = i * 30
        end = (i + 1) * 30
        xuid_string = ""
        for xuid in xuids[start:end]:
            xuid_string += f"xuid({xuid}),"
        xuid_string = xuid_string.rstrip(",")
        xuid_strings.append(xuid_string)
    return_dict = {"RewardTracks": []}
    with requests.Session() as s:
        for xuid_string in xuid_strings:
            response = s.get(
                f"https://economy.svc.halowaypoint.com:443/hi/careerranks/careerRank1?players={xuid_string}",
                headers=headers,
            )
            if response.status_code == 200:
                response_dict = response.json()
                return_dict.get("RewardTracks").extend(
                    response_dict.get("RewardTracks")
                )
    return return_dict
