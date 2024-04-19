import logging

from django.contrib.auth.models import User

from apps.discord.models import DiscordAccount
from apps.halo_infinite.models import HaloInfinitePlaylist
from apps.halo_infinite.utils import (
    get_career_ranks,
    get_contributor_xuids_for_maps_in_active_playlists,
    get_csrs,
)
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


def auto_verify_discord_xbox_live_link(
    discord_xbox_live_link: DiscordXboxLiveLink, user: User
) -> DiscordXboxLiveLink:
    # Evaluate Career Rank
    is_career_rank_nonzero = False
    career_rank_data = get_career_ranks([discord_xbox_live_link.xbox_live_account_id])
    xuid_career_rank_data = career_rank_data.get("career_ranks", {}).get(
        discord_xbox_live_link.xbox_live_account_id, {}
    )
    if xuid_career_rank_data.get("cumulative_score", 0) > 0:
        is_career_rank_nonzero = True

    # Evaluate peak CSR
    is_peak_csr_onyx = False
    current_ranked_playlists = HaloInfinitePlaylist.objects.filter(
        ranked=True, active=True
    ).order_by("name")
    for playlist in current_ranked_playlists:
        csr_data = get_csrs(
            [discord_xbox_live_link.xbox_live_account_id], playlist.playlist_id
        )
        xuid_csr_data = csr_data.get("csrs", {}).get(
            discord_xbox_live_link.xbox_live_account_id, {}
        )
        all_time_max_csr = xuid_csr_data.get("all_time_max_csr", -1)
        if all_time_max_csr >= 1500:
            is_peak_csr_onyx = True

    # Evaluate matchmaking map credits
    is_matchmaking_map_contributor = False
    if (
        discord_xbox_live_link.xbox_live_account_id
        in get_contributor_xuids_for_maps_in_active_playlists()
    ):
        is_matchmaking_map_contributor = True

    # Auto-verify if non-zero career rank, non-Onyx peak CSR, and non-matchmaking map contributor
    if (
        is_career_rank_nonzero
        and not is_peak_csr_onyx
        and not is_matchmaking_map_contributor
    ):
        discord_xbox_live_link.verified = True
        discord_xbox_live_link.verifier = user
        discord_xbox_live_link.save()

    return discord_xbox_live_link
