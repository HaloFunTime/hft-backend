import logging
import re

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.halo_infinite.api.match import match_stats
from apps.halo_infinite.constants import (
    GAME_VARIANT_CATEGORY_CAPTURE_THE_FLAG,
    GAME_VARIANT_CATEGORY_SLAYER,
    GAME_VARIANT_CATEGORY_STOCKPILE,
    GAME_VARIANT_CATEGORY_TOTAL_CONTROL,
)
from apps.season_04.models import (
    StampChallenge16Completion,
    StampChallenge17Completion,
    StampChallenge18Completion,
    StampChallenge19Completion,
    StampChallenge20Completion,
    StampChallengeBTBMatch,
)

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=StampChallengeBTBMatch)
def stamp_challenge_btb_match_pre_save(sender, instance, **kwargs):
    # Get match info for the Halo Infinite match
    stats = match_stats(instance.match_id)
    match_game_variant_category = stats.get("MatchInfo", {}).get("GameVariantCategory")
    match_playable_duration = stats.get("MatchInfo", {}).get("PlayableDuration")
    match_playable_minutes = int(
        re.search(r"\d+M", match_playable_duration).group().split("M")[0]
    )
    teams = stats.get("Teams", [])
    players = stats.get("Players", [])
    winning_team_id = None
    for team in teams:
        if team["Outcome"] == 2:
            winning_team_id = team.get("TeamId")

    # Perform a handful of challenge-specific validations
    if instance.challenge == StampChallengeBTBMatch.Challenges.FinishInFive:
        if (
            match_game_variant_category != GAME_VARIANT_CATEGORY_CAPTURE_THE_FLAG
            and match_game_variant_category != GAME_VARIANT_CATEGORY_SLAYER
            and match_game_variant_category != GAME_VARIANT_CATEGORY_STOCKPILE
            and match_game_variant_category != GAME_VARIANT_CATEGORY_TOTAL_CONTROL
        ):
            raise ValueError(
                "The match must be a non-Fiesta variant of CTF, Slayer, Stockpile, or Total Control."
            )
        if winning_team_id is None:
            raise ValueError("The match must have a winning team.")
        if match_playable_minutes >= 5:
            raise ValueError("The match must have taken less than five minutes.")
    elif instance.challenge == StampChallengeBTBMatch.Challenges.VictoryLap:
        if match_game_variant_category != GAME_VARIANT_CATEGORY_CAPTURE_THE_FLAG:
            raise ValueError("The match must be a non-Fiesta variant of CTF.")
        if winning_team_id is None:
            raise ValueError("The match must have a winning team.")
    elif instance.challenge == StampChallengeBTBMatch.Challenges.TypeA:
        if match_game_variant_category != GAME_VARIANT_CATEGORY_TOTAL_CONTROL:
            raise ValueError("The match must be a non-Fiesta variant of Total Control.")
        if winning_team_id is None:
            raise ValueError("The match must have a winning team.")
    elif instance.challenge == StampChallengeBTBMatch.Challenges.FormerlyChucks:
        if match_game_variant_category != GAME_VARIANT_CATEGORY_STOCKPILE:
            raise ValueError("The match must be a non-Fiesta variant of Stockpile.")
        if winning_team_id is None:
            raise ValueError("The match must have a winning team.")
    elif instance.challenge == StampChallengeBTBMatch.Challenges.InParticular:
        if match_game_variant_category != GAME_VARIANT_CATEGORY_SLAYER:
            raise ValueError("The match must be a non-Fiesta variant of Slayer.")
        players_with_deaths_by_team_id = {}
        players_with_deaths_by_team_id[teams[0].get("TeamId")] = 0
        players_with_deaths_by_team_id[teams[1].get("TeamId")] = 0
        for player in players:
            if (
                player.get("PlayerTeamStats")[0]
                .get("Stats")
                .get("CoreStats")
                .get("Deaths")
                > 0
            ):
                players_with_deaths_by_team_id[player.get("LastTeamId")] += 1
        if 1 not in players_with_deaths_by_team_id.values():
            raise ValueError("The match must have a team where only one player died.")


@receiver(post_save, sender=StampChallengeBTBMatch)
def stamp_challenge_btb_match_post_save(sender, instance, created, **kwargs):
    # Get match info for the Halo Infinite match
    stats = match_stats(instance.match_id)
    teams = stats.get("Teams", [])
    players = stats.get("Players", [])
    winning_team_id = None
    for team in teams:
        if team["Outcome"] == 2:
            winning_team_id = team.get("TeamId")

    # Create downstream records for the challenge
    if instance.challenge == StampChallengeBTBMatch.Challenges.FinishInFive:
        for player in players:
            if player.get("LastTeamId") == winning_team_id:
                xuid = int(re.search(r"\d+", player.get("PlayerId")).group())
                StampChallenge16Completion.objects.create(
                    creator=instance.creator,
                    match=instance,
                    xuid=xuid,
                )
    elif instance.challenge == StampChallengeBTBMatch.Challenges.VictoryLap:
        for player in players:
            if player.get("LastTeamId") == winning_team_id:
                xuid = int(re.search(r"\d+", player.get("PlayerId")).group())
                StampChallenge17Completion.objects.create(
                    creator=instance.creator,
                    match=instance,
                    xuid=xuid,
                )
    elif instance.challenge == StampChallengeBTBMatch.Challenges.TypeA:
        for player in players:
            if player.get("LastTeamId") == winning_team_id:
                xuid = int(re.search(r"\d+", player.get("PlayerId")).group())
                StampChallenge18Completion.objects.create(
                    creator=instance.creator,
                    match=instance,
                    xuid=xuid,
                )
    elif instance.challenge == StampChallengeBTBMatch.Challenges.FormerlyChucks:
        for player in players:
            if player.get("LastTeamId") == winning_team_id:
                xuid = int(re.search(r"\d+", player.get("PlayerId")).group())
                StampChallenge19Completion.objects.create(
                    creator=instance.creator,
                    match=instance,
                    xuid=xuid,
                )
    elif instance.challenge == StampChallengeBTBMatch.Challenges.InParticular:
        players_with_deaths_by_team_id = {}
        players_with_deaths_by_team_id[teams[0].get("TeamId")] = 0
        players_with_deaths_by_team_id[teams[1].get("TeamId")] = 0
        for player in players:
            if (
                player.get("PlayerTeamStats")[0]
                .get("Stats")
                .get("CoreStats")
                .get("Deaths")
                > 0
            ):
                players_with_deaths_by_team_id[player.get("LastTeamId")] += 1
        challenge_team_id = None
        for key in players_with_deaths_by_team_id.keys():
            if players_with_deaths_by_team_id[key] == 1:
                challenge_team_id = key
        for player in players:
            if player.get("LastTeamId") == challenge_team_id:
                xuid = int(re.search(r"\d+", player.get("PlayerId")).group())
                StampChallenge20Completion.objects.create(
                    creator=instance.creator,
                    match=instance,
                    xuid=xuid,
                )
