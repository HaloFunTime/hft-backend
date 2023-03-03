import logging

import requests

from apps.halo_infinite.decorators import spartan_token

logger = logging.getLogger(__name__)


@spartan_token
def recommended(**kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    with requests.Session() as s:
        response = s.get(
            "https://discovery-infiniteugc.svc.halowaypoint.com:443/hi/projects/712add52-f989-48e1-b3bb-ac7cd8a1c17a",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict
