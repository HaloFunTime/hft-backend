import logging
from uuid import UUID

import requests

from apps.halo_infinite.decorators import spartan_token

logger = logging.getLogger(__name__)


@spartan_token
def get_map(map_file_id: UUID, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    with requests.Session() as s:
        response = s.get(
            f"https://discovery-infiniteugc.svc.halowaypoint.com/hi/maps/{map_file_id}",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict


@spartan_token
def get_mode(mode_file_id: UUID, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    with requests.Session() as s:
        response = s.get(
            f"https://discovery-infiniteugc.svc.halowaypoint.com/hi/ugcGameVariants/{mode_file_id}",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict


@spartan_token
def get_prefab(prefab_file_id: UUID, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    with requests.Session() as s:
        response = s.get(
            f"https://discovery-infiniteugc.svc.halowaypoint.com/hi/prefabs/{prefab_file_id}",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict
