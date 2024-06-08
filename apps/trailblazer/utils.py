import datetime
import logging

from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.halo_infinite.constants import (
    GAME_VARIANT_CATEGORY_CAPTURE_THE_FLAG,
    GAME_VARIANT_CATEGORY_KING_OF_THE_HILL,
    GAME_VARIANT_CATEGORY_ODDBALL,
    GAME_VARIANT_CATEGORY_SLAYER,
    GAME_VARIANT_CATEGORY_STRONGHOLDS,
    LEVEL_ID_LIVE_FIRE,
    LEVEL_ID_STREETS,
)
from apps.halo_infinite.utils import (
    get_era_ranked_arena_matches_for_xuid,
    get_start_and_end_times_for_era,
)

logger = logging.getLogger(__name__)


def get_e1_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    start_time, end_time = get_start_and_end_times_for_era(1)
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        attendances=Count(
            "trailblazer_tuesday_attendees",
            distinct=True,
            filter=Q(
                trailblazer_tuesday_attendees__attendee_discord_id__in=discord_ids,
                trailblazer_tuesday_attendees__attendance_date__range=[
                    start_time.date(),
                    end_time.date() - datetime.timedelta(days=1),
                ],
            ),
        ),
    ).filter(discord_id__in=discord_ids)

    earn_dict = {}
    for account in annotated_discord_accounts:
        earn_dict[account.discord_id] = {
            "church_of_the_crab": min(account.attendances, 5) * 50,  # Max 5 per account
        }
    return earn_dict


def get_e1_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    earn_dict = {}
    for xuid in xuids:
        wins = 0
        slayer_wins = 0
        streets_wins = 0
        unlocked_hot_streak = False

        # Get matches for this XUID
        matches = get_era_ranked_arena_matches_for_xuid(xuid, 1)
        matches_sorted = sorted(
            matches,
            key=lambda m: datetime.datetime.fromisoformat(
                m.get("MatchInfo", {}).get("EndTime")
            ),
        )

        # CSR Go Up: Win games in Ranked Arena. 1 point per win.
        # Play to Slay: Win Slayer games in Ranked Arena. 5 points per win.
        # Mean Streets: Win games on the map Streets in Ranked Arena. 5 points per win.
        for match in matches:
            if match.get("Outcome") == 2:
                wins += 1
            if (
                match.get("MatchInfo", {}).get("GameVariantCategory")
                == GAME_VARIANT_CATEGORY_SLAYER
            ):
                if match.get("Outcome") == 2:
                    slayer_wins += 1
            if match.get("MatchInfo", {}).get("LevelId", {}) == LEVEL_ID_STREETS:
                if match.get("Outcome") == 2:
                    streets_wins += 1

        # Hot Streak: Win 3 consecutive Ranked Arena games and finish on top of the scoreboard each time. Earnable once.
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

        earn_dict[xuid] = {
            "csr_go_up": min(wins, 200),
            "play_to_slay": min(slayer_wins, 20) * 5,
            "mean_streets": min(streets_wins, 20) * 5,
            "hot_streak": 100 if unlocked_hot_streak else 0,
        }
    return earn_dict


def get_e2_discord_earn_dict(discord_ids: list[str]) -> dict[str, dict[str, int]]:
    start_time, end_time = get_start_and_end_times_for_era(2)
    annotated_discord_accounts = DiscordAccount.objects.annotate(
        attendances=Count(
            "trailblazer_tuesday_attendees",
            distinct=True,
            filter=Q(
                trailblazer_tuesday_attendees__attendee_discord_id__in=discord_ids,
                trailblazer_tuesday_attendees__attendance_date__range=[
                    start_time.date(),
                    end_time.date() - datetime.timedelta(days=1),
                ],
            ),
        ),
    ).filter(discord_id__in=discord_ids)

    earn_dict = {}
    for account in annotated_discord_accounts:
        earn_dict[account.discord_id] = {
            "church_of_the_crab": min(account.attendances, 5) * 50,  # Max 5 per account
        }
    return earn_dict


def get_e2_xbox_earn_dict(xuids: list[int]) -> dict[int, dict[str, int]]:
    earn_dict = {}
    for xuid in xuids:
        wins = 0
        strongholds_wins = 0
        live_fire_wins = 0
        unlocked_the_cycle = False

        # Get matches for this XUID
        matches = get_era_ranked_arena_matches_for_xuid(xuid, 2)
        matches_sorted = sorted(
            matches,
            key=lambda m: datetime.datetime.fromisoformat(
                m.get("MatchInfo", {}).get("EndTime")
            ),
        )

        # CSR Go Up: Win games in Ranked Arena. 1 point per win.
        # Too Stronk: Win Strongholds games in Ranked Arena. 5 points per win.
        # Scoreboard: Win games on the map Live Fire in Ranked Arena. 5 points per win.
        for match in matches:
            if match.get("Outcome") == 2:
                wins += 1
            if (
                match.get("MatchInfo", {}).get("GameVariantCategory")
                == GAME_VARIANT_CATEGORY_STRONGHOLDS
            ):
                if match.get("Outcome") == 2:
                    strongholds_wins += 1
            if match.get("MatchInfo", {}).get("LevelId", {}) == LEVEL_ID_LIVE_FIRE:
                if match.get("Outcome") == 2:
                    live_fire_wins += 1

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
                mode_category = win.get("MatchInfo", {}).get("GameVariantCategory")
                if mode_category == GAME_VARIANT_CATEGORY_CAPTURE_THE_FLAG:
                    ctf_win = True
                elif mode_category == GAME_VARIANT_CATEGORY_KING_OF_THE_HILL:
                    koth_win = True
                elif mode_category == GAME_VARIANT_CATEGORY_ODDBALL:
                    oddball_win = True
                elif mode_category == GAME_VARIANT_CATEGORY_SLAYER:
                    slayer_win = True
                elif mode_category == GAME_VARIANT_CATEGORY_STRONGHOLDS:
                    strongholds_win = True

            if ctf_win and koth_win and oddball_win and slayer_win and strongholds_win:
                unlocked_the_cycle = True
                break
            start_index += 1

        earn_dict[xuid] = {
            "csr_go_up": min(wins, 200),
            "too_stronk": min(strongholds_wins, 20) * 5,
            "scoreboard": min(live_fire_wins, 20) * 5,
            "the_cycle": 100 if unlocked_the_cycle else 0,
        }
    return earn_dict
