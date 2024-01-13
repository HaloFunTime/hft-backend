import requests

from apps.halo_infinite.decorators import clearance_token, spartan_token


@clearance_token
@spartan_token
def hi_api_get(
    url: str,
    session: requests.Session,
    use_spartan: bool = False,
    use_clearance: bool = False,
    **kwargs
) -> requests.Response:
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
    }
    if use_spartan:
        spartan_token = kwargs.get("HaloInfiniteSpartanToken")
        headers["x-343-authorization-spartan"] = spartan_token.token
    if use_clearance:
        clearance_token = kwargs.get("HaloInfiniteClearanceToken")
        headers["343-clearance"] = clearance_token.flight_configuration_id
    return session.get(url, headers=headers)
