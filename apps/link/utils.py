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
    verified: bool = False,
) -> DiscordXboxLiveLink:
    # NOTE: The following method call prioritizes the DiscordAccount, so that the XboxLiveAccount
    # associated with the DiscordAccount may be changed without errors.
    return DiscordXboxLiveLink.objects.update_or_create(
        discord_account=discord_account,
        defaults={
            "xbox_live_account": xbox_live_account,
            "creator": user,
            "verified": verified,
        },
    )[0]
