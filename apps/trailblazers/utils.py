import logging

from apps.halo_infinite.utils import get_csrs
from apps.link.models import DiscordXboxLiveLink

logger = logging.getLogger(__name__)


def get_sherpa_qualified(links: list[DiscordXboxLiveLink]) -> list[str]:
    sherpa_qualified_discord_ids = []
    xuid_to_discord_id = {
        link.xbox_live_account_id: link.discord_account_id for link in links
    }
    xuids = [link.xbox_live_account_id for link in links]

    # Someone qualifies as a Sherpa if they have a current reset max CSR of 1650 or greater in Ranked Arena
    csr_by_xuid = get_csrs(xuids, "edfef3ac-9cbe-4fa2-b949-8f29deafd483").get("csrs")
    sherpa_xuids = []
    for xuid in csr_by_xuid:
        if csr_by_xuid.get(xuid, {}).get("current_reset_max_csr", 0) >= 1650:
            sherpa_xuids.append(xuid)

    sherpa_qualified_discord_ids = [xuid_to_discord_id[xuid] for xuid in sherpa_xuids]
    return sherpa_qualified_discord_ids


def get_scout_qualified(links: list[DiscordXboxLiveLink]) -> list[str]:
    # TODO: Implement Scout logic
    scout_qualified_discord_ids = []
    return scout_qualified_discord_ids
