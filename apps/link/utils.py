import logging

from django.contrib.auth.models import User

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.xbox_live.models import XboxLiveAccount

logger = logging.getLogger(__name__)


def update_or_create_discord_xbox_live_link(
    discord_account: DiscordAccount,
    xbox_live_account: XboxLiveAccount,
    user: User,
) -> DiscordXboxLiveLink:
    verified = False
    verifier = None

    # If a DiscordXboxLiveLink record already exists with this DiscordAccount/XboxLiveAccount pair,
    # preserve its existing verification status.
    existing_link_record = (
        DiscordXboxLiveLink.objects.filter(discord_account=discord_account)
        .select_related("xbox_live_account")
        .first()
    )
    if (
        existing_link_record is not None
        and existing_link_record.xbox_live_account is not None
        and existing_link_record.xbox_live_account.xuid == xbox_live_account.xuid
    ):
        verified = existing_link_record.verified
        verifier = existing_link_record.verifier

    # Clear `verifier` if `verified` is false and we have an existing DiscordXboxLiveLink record.
    if existing_link_record is not None and not verified:
        verifier = None

    # NOTE: The following method call prioritizes the DiscordAccount, so that the XboxLiveAccount
    # associated with the DiscordAccount may be changed without errors.
    return DiscordXboxLiveLink.objects.update_or_create(
        discord_account=discord_account,
        defaults={
            "xbox_live_account": xbox_live_account,
            "verified": verified,
            "verifier": verifier,
            "creator": user,
        },
    )[0]
