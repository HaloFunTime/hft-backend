import requests

from apps.halo_infinite.api.utils import hi_api_get


def get_map_mode_pair(
    asset_id: str, version_id: str = None, session: requests.Session = None
):
    return_dict = {}
    close_session_before_exit = session is None
    s = requests.Session() if session is None else session
    url = (
        f"https://discovery-infiniteugc.svc.halowaypoint.com/hi/mapModePairs/{asset_id}"
    )
    if version_id is not None:
        url += f"/versions/{version_id}"
    response = hi_api_get(
        url,
        s,
        use_spartan=True,
        use_clearance=True,
    )
    if response.status_code == 200:
        return_dict = response.json()
    if close_session_before_exit:
        s.close()
    return return_dict
