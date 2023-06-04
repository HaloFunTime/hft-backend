import datetime
import logging

from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.halo_infinite.utils import (
    get_csr_after_match,
    get_csrs,
    get_current_season_id,
    get_first_and_last_days_for_season,
    get_season_ranked_arena_matches_for_xuid,
)

logger = logging.getLogger(__name__)

MODE_RANKED_CTF_ID = "507191c6-a492-4331-b2ae-a172101eb23e"
MODE_RANKED_KOTH_ID = "88c22b1f-2d64-48b9-bab1-26fe4721fb23"
MODE_RANKED_ODDBALL_ID = "751bcc9d-aace-45a1-8d71-358f0bc89f7e"
MODE_RANKED_SLAYER_ID = "c2d20d44-8606-4669-b894-afae15b3524f"
MODE_RANKED_STRONGHOLDS_ID = "22b8a0eb-0d02-4eb3-8f56-5f63fc254f83"


def get_s3_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    first_day, last_day = get_first_and_last_days_for_season("3")
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        attendances=Count(
            "trailblazer_tuesday_attendees",
            distinct=True,
            filter=Q(
                trailblazer_tuesday_attendees__attendee_discord_id__in=discord_ids,
                trailblazer_tuesday_attendees__attendance_date__range=[
                    first_day,
                    last_day,
                ],
            ),
        ),
        referrals=Count(
            "trailblazer_tuesday_referrers",
            distinct=True,
            filter=Q(
                trailblazer_tuesday_referrers__referrer_discord_id__in=discord_ids,
                trailblazer_tuesday_referrers__referral_date__range=[
                    first_day,
                    last_day,
                ],
            ),
        ),
        submissions=Count(
            "trailblazer_vod_submitters",
            distinct=True,
            filter=Q(
                trailblazer_vod_submitters__submitter_discord_id__in=discord_ids,
                trailblazer_vod_submitters__submission_date__range=[
                    first_day,
                    last_day,
                ],
            ),
        ),
    ).filter(discord_id__in=discord_ids)

    earn_dict = {}
    for account in annotated_discord_accounts:
        earn_dict[account.discord_id] = {
            "church_of_the_crab": min(account.attendances, 5) * 50,  # Max 5 per account
            "sharing_is_caring": min(account.referrals, 3) * 50,  # Max 3 per account
            "bookworm": min(account.submissions, 2) * 50,  # Max 2 per account
        }
    return earn_dict


def get_s3_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    # Get current CSRs for each XUID (needed for calculations)
    csr_by_xuid = get_csrs(xuids, "edfef3ac-9cbe-4fa2-b949-8f29deafd483").get("csrs")

    earn_dict = {}
    for xuid in xuids:
        unlocked_online_warrior = False
        unlocked_hot_streak = False
        oddball_wins = 0
        strongholds_wins = 0

        # Get matches for this XUID
        matches = get_season_ranked_arena_matches_for_xuid("3", xuid)
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
                unlocked_online_warrior = True

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
                unlocked_hot_streak = True
                break

        # Oddly Effective: Win 25 or more Oddball games
        # Too Stronk: Win 25 or more Strongholds games
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

        earn_dict[xuid] = {
            "online_warrior": 200 if unlocked_online_warrior else 0,
            "hot_streak": 100 if unlocked_hot_streak else 0,
            "oddly_effective": min(oddball_wins, 25) * 4,
            "too_stronk": min(strongholds_wins, 25) * 4,
        }
    return earn_dict


def is_s3_scout_qualified(discord_id: str, xuid: int | None) -> bool:
    points = 0

    # DISCORD CHALLENGES
    if discord_id is not None:
        discord_earn_dict = get_s3_discord_earn_dict([discord_id])
        earns = discord_earn_dict.get(discord_id)

        # Church of the Crab
        points += earns.get("church_of_the_crab")
        # Sharing is Caring
        points += earns.get("sharing_is_caring")
        # Bookworm
        points += earns.get("bookworm")

    # XBOX LIVE CHALLENGES
    if xuid is not None:
        xbox_earn_dict = get_s3_xbox_earn_dict([xuid])
        earns = xbox_earn_dict.get(xuid)

        # Online Warrior
        points += earns.get("online_warrior")
        # Hot Streak
        points += earns.get("hot_streak")
        # Oddly Effective
        points += earns.get("oddly_effective")
        # Too Stronk
        points += earns.get("too_stronk")

    logger.info(f"Scout Points for {discord_id}: {points}")
    return points >= 500


def get_s4_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    first_day, last_day = get_first_and_last_days_for_season("4")
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        attendances=Count(
            "trailblazer_tuesday_attendees",
            distinct=True,
            filter=Q(
                trailblazer_tuesday_attendees__attendee_discord_id__in=discord_ids,
                trailblazer_tuesday_attendees__attendance_date__range=[
                    first_day,
                    last_day,
                ],
            ),
        ),
        submissions=Count(
            "trailblazer_vod_submitters",
            distinct=True,
            filter=Q(
                trailblazer_vod_submitters__submitter_discord_id__in=discord_ids,
                trailblazer_vod_submitters__submission_date__range=[
                    first_day,
                    last_day,
                ],
            ),
        ),
        excellent_reviews=Count(
            "trailblazer_excellent_vod_reviewers",
            distinct=True,
            filter=Q(
                trailblazer_excellent_vod_reviewers__reviewer_discord_id__in=discord_ids,
                trailblazer_excellent_vod_reviewers__review_date__range=[
                    first_day,
                    last_day,
                ],
            ),
        ),
    ).filter(discord_id__in=discord_ids)

    earn_dict = {}
    for account in annotated_discord_accounts:
        earn_dict[account.discord_id] = {
            "church_of_the_crab": min(account.attendances, 5) * 50,  # Max 5 per account
            "bookworm": min(account.submissions, 3) * 50,  # Max 3 per account
            "film_critic": min(account.excellent_reviews, 1) * 100,  # Max 1 per account
        }
    return earn_dict


def get_s4_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    # Get current CSRs for each XUID (needed for calculations)
    csr_by_xuid = get_csrs(xuids, "edfef3ac-9cbe-4fa2-b949-8f29deafd483").get("csrs")

    earn_dict = {}
    for xuid in xuids:
        unlocked_online_warrior = False
        unlocked_the_cycle = False
        ctf_wins = 0
        koth_wins = 0

        # Get matches for this XUID
        matches = get_season_ranked_arena_matches_for_xuid("4", xuid)
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
                unlocked_online_warrior = True

        # The Cycle: Win at least one CTF, KotH, Oddball, Slayer, and Strongholds game in a six-hour period
        sorted_wins = []
        for match in matches_sorted:
            if match.get("Outcome") == 2:
                sorted_wins.append(match)
        start_index = 0
        while start_index < len(sorted_wins):
            ctf_win = False
            koth_win = False
            oddball_win = False
            slayer_win = False
            strongholds_win = False
            first_win = sorted_wins[start_index]
            start_time = datetime.datetime.fromisoformat(
                first_win.get("MatchInfo", {}).get("StartTime")
            )
            six_hours_after_start_time = start_time + datetime.timedelta(hours=6)
            wins_in_six_hour_window = [first_win]
            for i in range(start_index + 1, len(sorted_wins)):
                win = sorted_wins[i]
                if (
                    datetime.datetime.fromisoformat(
                        win.get("MatchInfo", {}).get("EndTime")
                    )
                    <= six_hours_after_start_time
                ):
                    wins_in_six_hour_window.append(win)
                else:
                    break
            for win in wins_in_six_hour_window:
                mode_id = (
                    win.get("MatchInfo", {}).get("UgcGameVariant", {}).get("AssetId")
                )
                if mode_id == MODE_RANKED_CTF_ID:
                    ctf_win = True
                elif mode_id == MODE_RANKED_KOTH_ID:
                    koth_win = True
                elif mode_id == MODE_RANKED_ODDBALL_ID:
                    oddball_win = True
                elif mode_id == MODE_RANKED_SLAYER_ID:
                    slayer_win = True
                elif mode_id == MODE_RANKED_STRONGHOLDS_ID:
                    strongholds_win = True

            if ctf_win and koth_win and oddball_win and slayer_win and strongholds_win:
                unlocked_the_cycle = True
                break
            start_index += 1

        # Checkered Flag: Win 25 or more Capture the Flag games
        # Them Thar Hills: Win 25 or more King of the Hill games
        for match in matches:
            if (
                match.get("MatchInfo", {}).get("UgcGameVariant", {}).get("AssetId")
                == MODE_RANKED_CTF_ID
            ):
                if match.get("Outcome") == 2:
                    ctf_wins += 1
            if (
                match.get("MatchInfo", {}).get("UgcGameVariant", {}).get("AssetId")
                == MODE_RANKED_KOTH_ID
            ):
                if match.get("Outcome") == 2:
                    koth_wins += 1

        earn_dict[xuid] = {
            "online_warrior": 200 if unlocked_online_warrior else 0,
            "the_cycle": 100 if unlocked_the_cycle else 0,
            "checkered_flag": min(ctf_wins, 25) * 4,
            "them_thar_hills": min(koth_wins, 25) * 4,
        }
    return earn_dict


def is_s4_scout_qualified(discord_id: str, xuid: int | None) -> bool:
    points = 0

    # DISCORD CHALLENGES
    if discord_id is not None:
        discord_earn_dict = get_s4_discord_earn_dict([discord_id])
        earns = discord_earn_dict.get(discord_id)

        # Church of the Crab
        points += earns.get("church_of_the_crab")
        # Bookworm
        points += earns.get("bookworm")
        # Film Critic
        points += earns.get("film_critic")

    # XBOX LIVE CHALLENGES
    if xuid is not None:
        xbox_earn_dict = get_s4_xbox_earn_dict([xuid])
        earns = xbox_earn_dict.get(xuid)

        # Online Warrior
        points += earns.get("online_warrior")
        # The Cycle
        points += earns.get("the_cycle")
        # Checkered Flag
        points += earns.get("checkered_flag")
        # Them Thar Hills
        points += earns.get("them_thar_hills")

    logger.info(f"Scout Points for {discord_id}: {points}")
    return points >= 500


def is_scout_qualified(discord_id: str, xuid: int | None) -> bool:
    season_id = get_current_season_id()
    if season_id == "3":
        return is_s3_scout_qualified(discord_id, xuid)
    elif season_id == "4":
        return is_s4_scout_qualified(discord_id, xuid)
    return False


def is_sherpa_qualified(xuid: int) -> bool:
    # Someone qualifies as a Sherpa if their linked gamertag has a current reset max CSR of 1650 or higher
    csr = (
        get_csrs([xuid], "edfef3ac-9cbe-4fa2-b949-8f29deafd483")
        .get("csrs")
        .get(xuid, {})
        .get("current_reset_max_csr", 0)
    )
    return csr >= 1650
