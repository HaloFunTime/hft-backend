import logging

import requests

from apps.halo_infinite.decorators import spartan_token

logger = logging.getLogger(__name__)


@spartan_token
def search_by_author(xuid: int, count: int = 25, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    results = []
    response_dict = {}
    with requests.Session() as s:
        more_results = True
        start = 0
        while more_results:
            # Grab results `count` at a time
            response = s.get(
                "https://discovery-infiniteugc.svc.halowaypoint.com/hi/search"
                f"?author=xuid({xuid})&count={count}&start={start}",
                headers=headers,
            )
            more_results = False
            if response.status_code == 200:
                response_dict = response.json()
                results.extend(response_dict.get("Results"))
                start += response_dict.get("Count")
                if start < response_dict.get("EstimatedTotal"):
                    more_results = True
    return results
