import datetime
import json
import logging

from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.halo_infinite.utils import (
    SEASON_3_END_DAY,
    SEASON_3_START_DAY,
    get_csr_after_match,
    get_csrs,
    get_season_3_ranked_arena_matches,
)
from apps.link.models import DiscordXboxLiveLink

logger = logging.getLogger(__name__)

MODE_RANKED_ODDBALL_ID = "751bcc9d-aace-45a1-8d71-358f0bc89f7e"
MODE_RANKED_STRONGHOLDS_ID = "22b8a0eb-0d02-4eb3-8f56-5f63fc254f83"


def get_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
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

    earn_dict = {}
    for account in annotated_discord_accounts:
        earn_dict[account.discord_id] = {
            "church_of_the_crab": min(account.attendances, 5),  # Max 5 per account
            "sharing_is_caring": min(account.referrals, 3),  # Max 3 per account
            "bookworm": min(account.submissions, 2),  # Max 2 per account
        }
    return earn_dict


def get_xbox_earn_sets(xuids: list[int]) -> tuple[set, set, set, set]:
    # Get current CSRs for each XUID (needed for calculations)
    csr_by_xuid = get_csrs(xuids, "edfef3ac-9cbe-4fa2-b949-8f29deafd483").get("csrs")

    # Initialize sets
    online_warrior_earn_set = set()
    hot_streak_earn_set = set()
    oddly_effective_earn_set = set()
    too_stronk_earn_set = set()
    for xuid in xuids:
        # Get matches for this XUID
        matches = get_season_3_ranked_arena_matches(xuid)
        matches_sorted = sorted(
            matches,
            key=lambda m: datetime.datetime.fromisoformat(
                m.get("MatchInfo", {}).get("StartTime")
            ),
        )

        # Online Warrior: Beat your placement CSR by 200 or more
        # Validate player has placed and we have at least 5 matches of data for them
        if csr_by_xuid[xuid]["current_csr"] != -1 and len(matches_sorted) >= 5:
            placement_match_index = 4
            placement_csr = None
            while placement_csr is None:
                placement_match = matches_sorted[placement_match_index]
                possible_placement_csr = get_csr_after_match(
                    xuid, placement_match.get("MatchId")
                )
                placement_csr = (
                    possible_placement_csr if possible_placement_csr != -1 else None
                )
                placement_match_index += 1
            if csr_by_xuid[xuid]["current_reset_max_csr"] >= placement_csr + 200:
                online_warrior_earn_set.add(xuid)

        # Hot Streak: Finish first on the postgame scoreboard in 3 consecutive games
        for i in range(len(matches_sorted) - 3):
            match_a = matches[i]
            match_b = matches[i + 1]
            match_c = matches[i + 2]
            if (
                match_a.get("Rank") == 1
                and match_b.get("Rank") == 1
                and match_c.get("Rank") == 1
            ):
                hot_streak_earn_set.add(xuid)
                break

        # Oddly Effective: Win 25 or more Oddball games
        # Too Stronk: Win 25 or more Strongholds games
        oddball_wins = 0
        strongholds_wins = 0
        for match in matches:
            if (
                match.get("MatchInfo", {}).get("UgcGameVariant", {}).get("AssetId")
                == MODE_RANKED_ODDBALL_ID
            ):
                if match.get("Outcome") == 2:
                    oddball_wins += 1
            if (
                match.get("MatchInfo", {}).get("UgcGameVariant", {}).get("AssetId")
                == MODE_RANKED_STRONGHOLDS_ID
            ):
                if match.get("Outcome") == 2:
                    strongholds_wins += 1
        if oddball_wins >= 25:
            oddly_effective_earn_set.add(xuid)
        if strongholds_wins >= 25:
            too_stronk_earn_set.add(xuid)

    return (
        online_warrior_earn_set,
        hot_streak_earn_set,
        oddly_effective_earn_set,
        too_stronk_earn_set,
    )


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
    discord_earn_dict = get_discord_earn_dict(discord_ids)
    for discord_id in discord_earn_dict:
        discord_points = 0
        earns = discord_earn_dict.get(discord_id)

        # Church of the Crab: 50 points each
        discord_points += earns.get("church_of_the_crab") * 50
        # Sharing is Caring: 50 points each
        discord_points += earns.get("sharing_is_caring") * 50
        # Bookworm: 50 points each
        discord_points += earns.get("bookworm") * 50

        points_by_discord_id[discord_id] = (
            points_by_discord_id[discord_id] + discord_points
        )

    # XBOX LIVE CHALLENGES
    xuids = [link.xbox_live_account_id for link in links]
    xuid_to_discord_id = {
        link.xbox_live_account_id: link.discord_account_id for link in links
    }

    (
        earned_online_warrior,
        earned_hot_streak,
        earned_oddly_effective,
        earned_too_stronk,
    ) = get_xbox_earn_sets(xuids)

    for xuid in xuids:
        xbox_points = 0
        # Online Warrior: 200 points each, max 1 per user
        if xuid in earned_online_warrior:
            xbox_points += 200
        # Hot Streak: 100 points each, max 1 per user
        if xuid in earned_hot_streak:
            xbox_points += 100
        # Oddly Effective: 100 points each, max 1 per user
        if xuid in earned_oddly_effective:
            xbox_points += 100
        # Too Stronk: 100 points each, max 1 per user
        if xuid in earned_too_stronk:
            xbox_points += 100

        discord_id = xuid_to_discord_id.get(xuid)
        points_by_discord_id[discord_id] = (
            points_by_discord_id[discord_id] + xbox_points
        )

    logger.info("Trailblazer Scout point totals (by Discord ID):")
    logger.info(json.dumps(points_by_discord_id))

    scout_qualified_discord_ids = [
        k for k, v in points_by_discord_id.items() if v >= 500
    ]
    return scout_qualified_discord_ids
