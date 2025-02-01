import logging

import requests
from django.contrib.auth.models import User

from apps.xbox_live.decorators import xsts_token
from apps.xbox_live.models import XboxLiveAccount

logger = logging.getLogger(__name__)


def update_or_create_xbox_live_account(gamertag: str, user: User) -> XboxLiveAccount:
    xuid_gamertag_tuple = get_xuid_and_exact_gamertag(gamertag)
    return XboxLiveAccount.objects.update_or_create(
        xuid=xuid_gamertag_tuple[0],
        defaults={"creator": user, "gamertag": xuid_gamertag_tuple[1]},
    )[0]


@xsts_token
def get_xuid_and_exact_gamertag(
    gamertag: str, **kwargs
) -> tuple[int | None, str | None]:
    assert gamertag is not None
    logger.debug(f"Called get_xuid_and_exact_gamertag with gamertag '{gamertag}'.")
    gamertag = gamertag.replace("#", "", 1)  # Replace first # with an empty space
    xsts_token = kwargs.get("XboxLiveXSTSToken")
    headers = {
        "Authorization": f"XBL3.0 x={xsts_token.uhs};{xsts_token.token}",
        "Content-Type": "application/json; charset=utf-8",
        "x-xbl-contract-version": "3",
    }
    with requests.Session() as s:
        xuid = None
        exact_gamertag = None
        try:
            params = {"settings": "Gamertag"}
            response = s.get(
                f"https://profile.xboxlive.com/users/gt({gamertag})/profile/settings",
                params=params,
                headers=headers,
            )
            resp_json = response.json()
            xuid = int(resp_json.get("profileUsers")[0].get("id"))
            exact_gamertag = (
                resp_json.get("profileUsers")[0].get("settings")[0].get("value")
            )
            logger.debug(f"XUID is {xuid}.")
            logger.debug(f"Exact gamertag is {exact_gamertag}.")
        except Exception:
            logger.debug("Failed to get XUID and exact gamertag.")
    return (xuid, exact_gamertag)


@xsts_token
def get_gamertag_from_xuid(xuid: int, **kwargs) -> str | None:
    assert xuid is not None
    logger.debug(f"Called get_gamertag_from_xuid with XUID '{xuid}'.")
    xsts_token = kwargs.get("XboxLiveXSTSToken")
    headers = {
        "Authorization": f"XBL3.0 x={xsts_token.uhs};{xsts_token.token}",
        "Content-Type": "application/json; charset=utf-8",
        "x-xbl-contract-version": "3",
    }
    with requests.Session() as s:
        gamertag = None
        try:
            params = {"settings": "Gamertag"}
            response = s.get(
                f"https://profile.xboxlive.com/users/xuid({xuid})/profile/settings",
                params=params,
                headers=headers,
            )
            resp_json = response.json()
            gamertag = resp_json.get("profileUsers")[0].get("settings")[0].get("value")
            logger.debug(f"Retrieved gamertag: {gamertag}")
        except Exception as ex:
            logger.debug("Failed to get gamertag from XUID.")
            logger.error(ex)
    return gamertag
