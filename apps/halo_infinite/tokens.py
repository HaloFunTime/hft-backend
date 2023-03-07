import datetime
import logging

import requests
from django.conf import settings

from apps.halo_infinite.exceptions import (
    HaloInfiniteClearanceTokenMissingException,
    HaloInfiniteSpartanTokenMissingException,
    HaloInfiniteXSTSTokenMissingException,
)
from apps.halo_infinite.models import (
    HaloInfiniteBuildID,
    HaloInfiniteClearanceToken,
    HaloInfiniteSpartanToken,
    HaloInfiniteXSTSToken,
)
from apps.xbox_live.models import XboxLiveUserToken
from apps.xbox_live.tokens import get_user_token

logger = logging.getLogger(__name__)


def generate_xsts_token(user_token: XboxLiveUserToken) -> HaloInfiniteXSTSToken | None:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-xbl-contract-version": "1",
    }
    payload = {
        "Properties": {"SandboxId": "RETAIL", "UserTokens": [user_token.token]},
        "RelyingParty": "https://prod.xsts.halowaypoint.com/",
        "TokenType": "JWT",
    }
    xsts_token = None
    with requests.Session() as s:
        response = s.post(
            "https://xsts.auth.xboxlive.com/xsts/authorize",
            json=payload,
            headers=headers,
        )
        if response.status_code == 200:
            # Create a new HaloInfiniteXSTSToken record
            response_dict = response.json()
            xsts_token = HaloInfiniteXSTSToken.objects.create(
                creator=user_token.creator,
                issue_instant=datetime.datetime.strptime(
                    f"{response_dict.get('IssueInstant')[:-9]}", "%Y-%m-%dT%H:%M:%S"
                ).replace(tzinfo=datetime.timezone.utc),
                not_after=datetime.datetime.strptime(
                    f"{response_dict.get('NotAfter')[:-9]}", "%Y-%m-%dT%H:%M:%S"
                ).replace(tzinfo=datetime.timezone.utc),
                token=response_dict.get("Token"),
                uhs=response_dict.get("DisplayClaims").get("xui")[0].get("uhs"),
            )
    return xsts_token


def get_xsts_token() -> HaloInfiniteXSTSToken:
    # Get the freshest HaloInfiniteXSTSToken from the DB.
    xsts_token = HaloInfiniteXSTSToken.objects.order_by("-not_after").first()

    # If there is no token, or the token exists but is expired, try generating a new one
    if not xsts_token or (xsts_token and xsts_token.expired):
        logger.info("Attempting to generate new HaloInfiniteXSTSToken")
        # Retrieve an XboxLiveUserToken (needed for generating a new XSTS token)
        user_token = get_user_token()
        xsts_token = generate_xsts_token(user_token)

    # If we get to this point with an unexpired token, return it
    if xsts_token and not xsts_token.expired:
        return xsts_token

    raise HaloInfiniteXSTSTokenMissingException(
        "Could not retrieve an unexpired HaloInfiniteXSTSToken."
    )


def generate_spartan_token(
    xsts_token: HaloInfiniteXSTSToken,
) -> HaloInfiniteSpartanToken | None:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
    }
    payload = {
        "Audience": "urn:343:s3:services",
        "MinVersion": "4",
        "Proof": [{"Token": xsts_token.token, "TokenType": "Xbox_XSTSv3"}],
    }
    spartan_token = None
    with requests.Session() as s:
        response = s.post(
            "https://settings.svc.halowaypoint.com/spartan-token",
            json=payload,
            headers=headers,
        )
        if response.status_code == 201:
            # Create a new HaloInfiniteSpartanToken record
            response_dict = response.json()
            spartan_token = HaloInfiniteSpartanToken.objects.create(
                creator=xsts_token.creator,
                expires_utc=datetime.datetime.strptime(
                    response_dict.get("ExpiresUtc").get("ISO8601Date")[:-5],
                    "%Y-%m-%dT%H:%M:%S",
                ).replace(tzinfo=datetime.timezone.utc),
                token=response_dict.get("SpartanToken"),
                token_duration=response_dict.get("TokenDuration"),
            )
    return spartan_token


def get_spartan_token() -> HaloInfiniteSpartanToken:
    # Get the freshest HaloInfiniteSpartanToken from the DB.
    spartan_token = HaloInfiniteSpartanToken.objects.order_by("-expires_utc").first()

    # If there is no token, or the token exists but is expired, try generating a new one
    if not spartan_token or (spartan_token and spartan_token.expired):
        logger.info("Attempting to generate new HaloInfiniteSpartanToken")
        # Retrieve a HaloInfiniteXSTSToken (needed for generating a new Spartan token)
        xsts_token = get_xsts_token()
        spartan_token = generate_spartan_token(xsts_token)

    # If we get to this point with an unexpired token, return it
    if spartan_token and not spartan_token.expired:
        return spartan_token

    raise HaloInfiniteSpartanTokenMissingException(
        "Could not retrieve an unexpired HaloInfiniteSpartanToken."
    )


def generate_clearance_token(
    spartan_token: HaloInfiniteSpartanToken,
    xuid: str,
    build_id: str,
) -> HaloInfiniteClearanceToken | None:
    headers = {
        "Accept": "application/json",
        "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
        "x-343-authorization-spartan": spartan_token.token,
    }
    clearance_token = None
    with requests.Session() as s:
        response = s.get(
            "https://settings.svc.halowaypoint.com/oban/flight-configurations/titles/hi/audiences/RETAIL/players/"
            f"xuid({xuid})/active?sandbox=UNUSED&build={build_id}",
            headers=headers,
        )
        if response.status_code == 200:
            response_dict = response.json()
            clearance_token = HaloInfiniteClearanceToken.objects.create(
                creator=spartan_token.creator,
                flight_configuration_id=response_dict.get("FlightConfigurationId"),
            )
    return clearance_token


def get_clearance_token() -> HaloInfiniteClearanceToken:
    # Get the freshest HaloInfiniteClearanceToken from the DB.
    clearance_token = HaloInfiniteClearanceToken.objects.order_by("-created_at").first()

    # If there is no token, or the token exists but is expired, try generating a new one
    if not clearance_token or (clearance_token and clearance_token.expired):
        logger.info("Attempting to generate new HaloInfiniteClearanceToken")
        # Retrieve a HaloInfiniteSpartanToken, XUID, and Build ID (needed for generating a new Clearance token)
        spartan_token = get_spartan_token()
        xuid = settings.INTERN_XUID
        most_recent_build = HaloInfiniteBuildID.objects.order_by("-build_date").first()
        clearance_token = generate_clearance_token(
            spartan_token, xuid, most_recent_build.build_id
        )

    # If we get to this point with an unexpired token, return it
    if clearance_token and not clearance_token.expired:
        return clearance_token

    raise HaloInfiniteClearanceTokenMissingException(
        "Could not retrieve an unexpired HaloInfiniteClearanceToken."
    )
