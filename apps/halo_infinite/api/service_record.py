import logging

import requests

from apps.halo_infinite.decorators import spartan_token

logger = logging.getLogger(__name__)


@spartan_token
def service_record(xuid: int, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    with requests.Session() as s:
        response = s.get(
            f"https://halostats.svc.halowaypoint.com/hi/players/xuid({xuid})/matchmade/servicerecord",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict
