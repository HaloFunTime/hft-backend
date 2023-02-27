import logging

import requests

from apps.halo_infinite.decorators import clearance_token, spartan_token

logger = logging.getLogger(__name__)

# Ranked Playlist: edfef3ac-9cbe-4fa2-b949-8f29deafd483


@clearance_token
@spartan_token
def csr(xuids: list[int], playlist_id: str, **kwargs) -> dict:
    spartan_token = kwargs.get("HaloInfiniteSpartanToken")
    clearance_token = kwargs.get("HaloInfiniteClearanceToken")
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
        "343-clearance": clearance_token.flight_configuration_id,
    }
    xuid_string = ""
    for xuid in xuids:
        xuid_string += f"xuid({xuid}),"
    xuid_string = xuid_string.rstrip(",")
    return_dict = {}
    with requests.Session() as s:
        response = s.get(
            f"https://skill.svc.halowaypoint.com:443/hi/playlist/{playlist_id}/csrs?players={xuid_string}",
            headers=headers,
        )
        if response.status_code == 200:
            return_dict = response.json()
    return return_dict


# https://discovery-infiniteugc.svc.halowaypoint.com:443
#   /hi/projects/712add52-f989-48e1-b3bb-ac7cd8a1c17a - Get 343 Recommended
#   /hi/projects/a9dc0785-2a99-4fec-ba6e-0216feaaf041 - Get Custom Game Manifest
#   /hi/engineGameVariants/{assetId}/versions/{versionId} - Get Engine Game Variant
#   /hi/engineGameVariants/{assetId} - Get Engine Game Variant Without Version
#   /hi/films/{assetId} - Get Film
#   /hi/projects/bf0e9bab-6fed-47a4-8bf7-bfd4422ee552 - Get Forge Templates
#   /hi/manifests/{assetId}/versions/{versionId}} - Get Manifest
#   /hi/manifests/branches/{branchName}/game - Get Manifest By Branch
#   /hi/manifests/builds/{buildNumber}/game - Get Manifest By Build
#   /hi/manifests/guids/{buildGuid}/game - Get Manifest By Build GUID
#   /hi/manifests/{assetId} - Get Manifest Without Version
#   /hi/maps/{assetId}/versions/{versionId} - Get Map
#   /hi/mapModePairs/{assetId}/versions/{versionId} - Get Map Mode Pair
#   /hi/mapModePairs/{assetId} - Get Map Mode Pair Without Version
#   /hi/maps/{assetId} - Get Map Without Version
#   /hi/playlists/{assetId}/versions/{versionId} - Get Playlist
#   /hi/playlists/{assetId} - Get Playlist Without Version
#   /hi/prefabs/{assetId}/versions/{versionId} - Get Prefab
#   /hi/prefabs/{assetId} - Get Prefab Without Version
#   /hi/projects/{assetId}/versions/{versionId} - Get Project
#   /hi/projects/{assetId} - Get Project Without Version
#   /hi/info/tags - Get Tags Info
#   /hi/ugcGameVariants/{assetId}/versions/{versionId} - Get UGC Game Variant
#   /hi/ugcGameVariants/{assetId} - Get UGC Game Variant Without Version
#   /hi/search - Search
#   /hi/films/matches/{matchId}/spectate - Spectate By Match Id
