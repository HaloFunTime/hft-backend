import datetime
import logging

import requests
from django.conf import settings

from apps.xbox_live.exceptions import (
    XboxLiveOAuthTokenMissingException,
    XboxLiveUserTokenMissingException,
    XboxLiveXSTSTokenMissingException,
)
from apps.xbox_live.models import (
    XboxLiveOAuthToken,
    XboxLiveUserToken,
    XboxLiveXSTSToken,
)

logger = logging.getLogger(__name__)


def refresh_oauth_token(
    existing_oauth_token: XboxLiveOAuthToken,
) -> XboxLiveOAuthToken | None:
    token_request_content = {
        "grant_type": "refresh_token",
        "refresh_token": existing_oauth_token.refresh_token,
        "approval_prompt": "auto",
        "redirect_uri": "http://localhost/auth/callback",
        "client_id": settings.AZURE_CLIENT_ID,
        "client_secret": settings.AZURE_CLIENT_SECRET,
        "scope": existing_oauth_token.scope,
    }
    oauth_token = None
    with requests.Session() as s:
        response = s.post(
            "https://login.live.com/oauth20_token.srf", data=token_request_content
        )
        if response.status_code == 200:
            # Create a new XboxLiveOAuthToken record
            response_dict = response.json()
            oauth_token = XboxLiveOAuthToken.objects.create(
                creator=existing_oauth_token.creator,
                token_type=response_dict.get("token_type"),
                expires_in=response_dict.get("expires_in"),
                scope=response_dict.get("scope"),
                access_token=response_dict.get("access_token"),
                refresh_token=response_dict.get("refresh_token"),
                user_id=response_dict.get("user_id"),
            )
    return oauth_token


def get_oauth_token() -> XboxLiveOAuthToken:
    # Get the freshest XboxLiveOAuthToken from the DB
    # NOTE: Since expiration is calculated from `created_at` + `expires_in`, neither of which should change, querying
    # in descending `created_at` order allows us to get the token with most recent expiration datetime.
    oauth_token = XboxLiveOAuthToken.objects.order_by("-created_at").first()

    # If the token is expired but potentially refreshable, try refreshing it
    if oauth_token and oauth_token.expired and oauth_token.refresh_token:
        logger.info("Attempting to refresh XboxLiveOAuthToken")
        oauth_token = refresh_oauth_token(oauth_token)

    # If we get to this point with an unexpired token, return it
    if oauth_token and not oauth_token.expired:
        return oauth_token

    raise XboxLiveOAuthTokenMissingException(
        "Could not retrieve an unexpired XboxLiveOAuthToken."
    )


def generate_user_token(oauth_token: XboxLiveOAuthToken) -> XboxLiveUserToken | None:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-xbl-contract-version": "1",
    }
    payload = {
        "Properties": {
            "AuthMethod": "RPS",
            "RpsTicket": f"d={oauth_token.access_token}",
            "SiteName": "user.auth.xboxlive.com",
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT",
    }
    user_token = None
    with requests.Session() as s:
        response = s.post(
            "https://user.auth.xboxlive.com/user/authenticate",
            json=payload,
            headers=headers,
        )
        if response.status_code == 200:
            # Create a new XboxLiveUserToken record
            response_dict = response.json()
            user_token = XboxLiveUserToken.objects.create(
                creator=oauth_token.creator,
                issue_instant=datetime.datetime.strptime(
                    f"{response_dict.get('IssueInstant')[:-9]}", "%Y-%m-%dT%H:%M:%S"
                ).replace(tzinfo=datetime.timezone.utc),
                not_after=datetime.datetime.strptime(
                    f"{response_dict.get('NotAfter')[:-9]}", "%Y-%m-%dT%H:%M:%S"
                ).replace(tzinfo=datetime.timezone.utc),
                token=response_dict.get("Token"),
                uhs=response_dict.get("DisplayClaims").get("xui")[0].get("uhs"),
            )
    return user_token


def get_user_token() -> XboxLiveUserToken:
    # Get the freshest XboxLiveUserToken from the DB
    user_token = XboxLiveUserToken.objects.order_by("-not_after").first()

    # If there is no token, or the token exists but is expired, try generating a new one
    if not user_token or (user_token and user_token.expired):
        logger.info("Attempting to generate new XboxLiveUserToken")
        # Retrieve an XboxLiveOAuthToken (needed for generating a new User token)
        oauth_token = get_oauth_token()
        user_token = generate_user_token(oauth_token)

    # If we get to this point with an unexpired token, return it
    if user_token and not user_token.expired:
        return user_token

    raise XboxLiveUserTokenMissingException(
        "Could not retrieve an unexpired XboxLiveUserToken."
    )


def generate_xsts_token(user_token: XboxLiveUserToken) -> XboxLiveXSTSToken | None:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-xbl-contract-version": "1",
    }
    payload = {
        "Properties": {"SandboxId": "RETAIL", "UserTokens": [user_token.token]},
        "RelyingParty": "http://xboxlive.com",
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
            # Create a new XboxLiveXSTSToken record
            response_dict = response.json()
            xsts_token = XboxLiveXSTSToken.objects.create(
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


def get_xsts_token() -> XboxLiveXSTSToken:
    # Get the freshest XboxLiveXSTSToken from the DB.
    xsts_token = XboxLiveXSTSToken.objects.order_by("-not_after").first()

    # If there is no token, or the token exists but is expired, try generating a new one
    if not xsts_token or (xsts_token and xsts_token.expired):
        logger.info("Attempting to generate new XboxLiveXSTSToken")
        # Retrieve an XboxLiveUserToken (needed for generating a new XSTS token)
        user_token = get_user_token()
        xsts_token = generate_xsts_token(user_token)

    # If we get to this point with an unexpired token, return it
    if xsts_token and not xsts_token.expired:
        return xsts_token

    raise XboxLiveXSTSTokenMissingException(
        "Could not retrieve an unexpired XboxLiveXSTSToken."
    )
