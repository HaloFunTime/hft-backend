import logging

import requests

from apps.xbox_live.decorators import xsts_token
from apps.xbox_live.models import XboxLiveAccount

logger = logging.getLogger(__name__)


def get_or_create_xbox_live_account(gamertag):
    try:
        existing_xbox_live_account = XboxLiveAccount.objects.get(gamertag=gamertag)
        return existing_xbox_live_account
    except XboxLiveAccount.DoesNotExist:
        pass
    return XboxLiveAccount.objects.create(
        gamertag=gamertag, xuid=get_xuid_for_gamertag(gamertag)
    )


@xsts_token
def get_xuid_for_gamertag(gamertag: str, **kwargs) -> str | None:
    logger.debug(f"Called get_xuid_for_gamertag with gamertag '{gamertag}'.")
    xsts_token = kwargs.get("XboxLiveXSTSToken")
    headers = {
        "Authorization": f"XBL3.0 x={xsts_token.uhs};{xsts_token.token}",
        "Content-Type": "application/json; charset=utf-8",
        "x-xbl-contract-version": "3",
    }
    with requests.Session() as s:
        xuid = None
        try:
            response = s.get(
                f"https://profile.xboxlive.com/users/gt({gamertag})/profile/settings",
                headers=headers,
            )
            xuid = response.json().get("profileUsers")[0].get("id")
            logger.debug(f"XUID is {xuid}.")
        except Exception:
            logger.debug("Failed to get XUID.")
    return xuid
