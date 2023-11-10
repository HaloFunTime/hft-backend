import logging
from uuid import UUID

import requests

from apps.halo_infinite.decorators import spartan_token

logger = logging.getLogger(__name__)


@spartan_token
def get_map(map_asset_id: UUID, map_version_id: UUID = None, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    route = f"hi/maps/{map_asset_id}"
    if map_version_id is not None:
        route += f"/versions/{map_version_id}"
    with requests.Session() as s:
        response = s.get(
            f"https://discovery-infiniteugc.svc.halowaypoint.com/{route}",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict


@spartan_token
def get_mode(mode_asset_id: UUID, mode_version_id: UUID = None, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    route = f"hi/ugcGameVariants/{mode_asset_id}"
    if mode_version_id is not None:
        route += f"/versions/{mode_version_id}"
    with requests.Session() as s:
        response = s.get(
            f"https://discovery-infiniteugc.svc.halowaypoint.com/{route}",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict


@spartan_token
def get_playlist(
    playlist_asset_id: UUID, playlist_version_id: UUID = None, **kwargs
) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    return_dict = {}
    route = f"hi/playlists/{playlist_asset_id}"
    if playlist_version_id is not None:
        route += f"/versions/{playlist_version_id}"
    with requests.Session() as s:
        response = s.get(
            f"https://discovery-infiniteugc.svc.halowaypoint.com/{route}",
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
