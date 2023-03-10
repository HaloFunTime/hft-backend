import datetime
import json
import logging

from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.halo_infinite.utils import get_csrs
from apps.link.models import DiscordXboxLiveLink

logger = logging.getLogger(__name__)

SEASON_3_START_DAY = datetime.date(year=2023, month=3, day=7)
SEASON_3_END_DAY = datetime.date(year=2023, month=6, day=26)


def earned_online_warrior(xuid: int) -> bool:
    return False


def earned_clean_sweep(xuid: int) -> bool:
    return False


def get_sherpa_qualified(links: list[DiscordXboxLiveLink]) -> list[str]:
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


def get_scout_qualified(
    discord_ids: list[str], links: list[DiscordXboxLiveLink]
) -> list[str]:
    points_by_discord_id = {discord_id: 0 for discord_id in discord_ids}

    # DISCORD CHALLENGES
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        attendances=Count(
            "trailblazer_tuesday_attendees",
            filter=Q(
                trailblazer_tuesday_attendees__attendee_discord_id__in=discord_ids,
                trailblazer_tuesday_attendees__attendance_date__range=[
                    SEASON_3_START_DAY,
                    SEASON_3_END_DAY,
                ],
            ),
        ),
        referrals=Count(
            "trailblazer_tuesday_referrers",
            filter=Q(
                trailblazer_tuesday_referrers__referrer_discord_id__in=discord_ids,
                trailblazer_tuesday_referrers__referral_date__range=[
                    SEASON_3_START_DAY,
                    SEASON_3_END_DAY,
                ],
            ),
        ),
        submissions=Count(
            "trailblazer_vod_submitters",
            filter=Q(
                trailblazer_vod_submitters__submitter_discord_id__in=discord_ids,
                trailblazer_vod_submitters__submission_date__range=[
                    SEASON_3_START_DAY,
                    SEASON_3_END_DAY,
                ],
            ),
        ),
    ).filter(discord_id__in=discord_ids)

    for discord_account in annotated_discord_accounts:
        discord_points = 0
        # Church of the Crab: 50 points each, max 5 per account
        discord_points += min(discord_account.attendances, 5) * 50
        # Sharing is Caring: 50 points each, no per-account max
        discord_points += discord_account.referrals * 50
        # Bookworm: 50 points each, max of 2 per account
        discord_points += min(discord_account.submissions, 2) * 50

        points_by_discord_id[discord_account.discord_id] = (
            points_by_discord_id[discord_account.discord_id] + discord_points
        )

    # XBOX LIVE CHALLENGES
    xuids = [link.xbox_live_account_id for link in links]
    xuid_to_discord_id = {
        link.xbox_live_account_id: link.discord_account_id for link in links
    }

    for xuid in xuids:
        xbox_points = 0
        # Online Warrior: 200 points each, max 1 per user
        if earned_online_warrior(xuid):
            xbox_points += 200
        # Clean Sweep: 200 points each, max 1 per user
        if earned_clean_sweep(xuid):
            xbox_points += 200

        discord_id = xuid_to_discord_id.get(xuid)
        points_by_discord_id[discord_id] = (
            points_by_discord_id[discord_id] + xbox_points
        )

    logger.info("Trailblazer Scout point totals by Discord ID:")
    logger.info(json.dumps(points_by_discord_id))

    scout_qualified_discord_ids = [
        k for k, v in points_by_discord_id.items() if v >= 500
    ]
    return scout_qualified_discord_ids
