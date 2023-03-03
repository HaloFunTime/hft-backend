import logging

from apps.halo_infinite.utils import get_343_recommended_file_contributors
from apps.link.models import DiscordXboxLiveLink

logger = logging.getLogger(__name__)


def get_illuminated_qualified(links: list[DiscordXboxLiveLink]) -> list[str]:
    illuminated_qualified_discord_ids = []
    xuid_to_discord_id = {
        link.xbox_live_account_id: link.discord_account_id for link in links
    }

    # Someone qualifies as Illuminated if their linked gamertag contributed to at least one file on 343's Recommended
    contributor_dict = get_343_recommended_file_contributors()
    illuminated_xuids = []
    for xuid in contributor_dict:
        # If the XUID from 343 recommended matches an XUID from one of our link records, they have qualified
        if xuid in xuid_to_discord_id:
            illuminated_xuids.append(xuid)

    illuminated_qualified_discord_ids = [
        xuid_to_discord_id[xuid] for xuid in illuminated_xuids
    ]
    return illuminated_qualified_discord_ids


def get_dynamo_qualified(links: list[DiscordXboxLiveLink]) -> list[str]:
    # TODO: Implement Dynamo logic
    dynamo_qualified_discord_ids = []
    return dynamo_qualified_discord_ids
