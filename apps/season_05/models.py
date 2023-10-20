from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.discord.models import DiscordAccount
from apps.halo_infinite.models import HaloInfinitePlaylist
from apps.overrides.models import Base


class DomainChallengeTeamAssignment(Base):
    class Meta:
        db_table = "DomainChallengeTeamAssignment"
        ordering = ["-created_at"]
        verbose_name = "Team Assignment"
        verbose_name_plural = "Team Assignments"

    class Teams(models.TextChoices):
        FunTimeBot = "FunTimeBot", _("Team FunTimeBot")
        HFT_Intern = "HFT Intern", _("Team HFT Intern")
        Unassigned = "Unassigned", _("Unassigned")

    assignee = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        related_name="assignees",
        verbose_name="Assignee",
    )
    team = models.CharField(max_length=10, choices=Teams.choices)

    def __str__(self):
        return f"{self.assignee} ({self.team})"


class DomainChallengeTeamReassignment(Base):
    class Meta:
        db_table = "DomainChallengeTeamReassignment"
        ordering = ["-created_at"]
        verbose_name = "Team Reassignment"
        verbose_name_plural = "Team Reassignments"

    reassignee = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        related_name="reassignees",
        verbose_name="Reassignee",
    )
    next_team = models.CharField(
        max_length=10,
        choices=DomainChallengeTeamAssignment.Teams.choices,
        verbose_name="Next Team",
    )
    reassignment_date = models.DateField(verbose_name="Reassignment Date")
    reason = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.reassignee} switches to {self.next_team} on {self.reassignment_date}"


class Domain(Base):
    class Meta:
        db_table = "Domain"
        ordering = ["effective_date", "created_at"]
        verbose_name = "Domain"
        verbose_name_plural = "Domains"

    class Stats(models.TextChoices):
        MatchesCompleted = "MatchesCompleted", _("MatchesCompleted")
        Wins = "Wins", _("Wins")
        Losses = "Losses", _("Losses")
        Ties = "Ties", _("Ties")
        CoreStats_Score = "CoreStats_Score", _("Score")
        CoreStats_PersonalScore = "CoreStats_PersonalScore", _("PersonalScore")
        CoreStats_RoundsWon = "CoreStats_RoundsWon", _("RoundsWon")
        CoreStats_RoundsLost = "CoreStats_RoundsLost", _("RoundsLost")
        CoreStats_RoundsTied = "CoreStats_RoundsTied", _("RoundsTied")
        CoreStats_Kills = "CoreStats_Kills", _("Kills")
        CoreStats_Deaths = "CoreStats_Deaths", _("Deaths")
        CoreStats_Assists = "CoreStats_Assists", _("Assists")
        CoreStats_Suicides = "CoreStats_Suicides", _("Suicides")
        CoreStats_Betrayals = "CoreStats_Betrayals", _("Betrayals")
        CoreStats_GrenadeKills = "CoreStats_GrenadeKills", _("GrenadeKills")
        CoreStats_HeadshotKills = "CoreStats_HeadshotKills", _("HeadshotKills")
        CoreStats_MeleeKills = "CoreStats_MeleeKills", _("MeleeKills")
        CoreStats_PowerWeaponKills = "CoreStats_PowerWeaponKills", _("PowerWeaponKills")
        CoreStats_ShotsFired = "CoreStats_ShotsFired", _("ShotsFired")
        CoreStats_ShotsHit = "CoreStats_ShotsHit", _("ShotsHit")
        CoreStats_DamageDealt = "CoreStats_DamageDealt", _("DamageDealt")
        CoreStats_DamageTaken = "CoreStats_DamageTaken", _("DamageTaken")
        CoreStats_CalloutAssists = "CoreStats_CalloutAssists", _("CalloutAssists")
        CoreStats_VehicleDestroys = "CoreStats_VehicleDestroys", _("VehicleDestroys")
        CoreStats_DriverAssists = "CoreStats_DriverAssists", _("DriverAssists")
        CoreStats_Hijacks = "CoreStats_Hijacks", _("Hijacks")
        CoreStats_EmpAssists = "CoreStats_EmpAssists", _("EmpAssists")
        CoreStats_MaxKillingSpree = "CoreStats_MaxKillingSpree", _("MaxKillingSpree")
        CoreStats_Medals = "CoreStats_Medals", _("Medal Count")
        CaptureTheFlagStats_FlagCaptureAssists = (
            "CaptureTheFlagStats_FlagCaptureAssists",
            _("CTF: FlagCaptureAssists"),
        )
        CaptureTheFlagStats_FlagCaptures = "CaptureTheFlagStats_FlagCaptures", _(
            "CTF: FlagCaptures"
        )
        CaptureTheFlagStats_FlagCarriersKilled = (
            "CaptureTheFlagStats_FlagCarriersKilled",
            _("CTF: FlagCarriersKilled"),
        )
        CaptureTheFlagStats_FlagGrabs = "CaptureTheFlagStats_FlagGrabs", _(
            "CTF: FlagGrabs"
        )
        CaptureTheFlagStats_FlagReturnersKilled = (
            "CaptureTheFlagStats_FlagReturnersKilled",
            _("CTF: FlagReturnersKilled"),
        )
        CaptureTheFlagStats_FlagReturns = "CaptureTheFlagStats_FlagReturns", _(
            "CTF: FlagReturns"
        )
        CaptureTheFlagStats_FlagSecures = "CaptureTheFlagStats_FlagSecures", _(
            "CTF: FlagSecures"
        )
        CaptureTheFlagStats_FlagSteals = "CaptureTheFlagStats_FlagSteals", _(
            "CTF: FlagSteals"
        )
        CaptureTheFlagStats_KillsAsFlagCarrier = (
            "CaptureTheFlagStats_KillsAsFlagCarrier",
            _("CTF: KillsAsFlagCarrier"),
        )
        CaptureTheFlagStats_KillsAsFlagReturner = (
            "CaptureTheFlagStats_KillsAsFlagReturner",
            _("CTF: KillsAsFlagReturner"),
        )
        EliminationStats_AlliesRevived = "EliminationStats_AlliesRevived", _(
            "Elimination: AlliesRevived"
        )
        EliminationStats_EliminationAssists = "EliminationStats_EliminationAssists", _(
            "Elimination: EliminationAssists"
        )
        EliminationStats_Eliminations = "EliminationStats_Eliminations", _(
            "Elimination: Eliminations"
        )
        EliminationStats_EnemyRevivesDenied = "EliminationStats_EnemyRevivesDenied", _(
            "Elimination: EnemyRevivesDenied"
        )
        EliminationStats_Executions = "EliminationStats_Executions", _(
            "Elimination: Executions"
        )
        EliminationStats_KillsAsLastPlayerStanding = (
            "EliminationStats_KillsAsLastPlayerStanding",
            _("Elimination: KillsAsLastPlayerStanding"),
        )
        EliminationStats_LastPlayersStandingKilled = (
            "EliminationStats_LastPlayersStandingKilled",
            _("Elimination: LastPlayersStandingKilled"),
        )
        EliminationStats_RoundsSurvived = "EliminationStats_RoundsSurvived", _(
            "Elimination: RoundsSurvived"
        )
        EliminationStats_TimesRevivedByAlly = "EliminationStats_TimesRevivedByAlly", _(
            "Elimination: TimesRevivedByAlly"
        )
        ExtractionStats_SuccessfulExtractions = (
            "ExtractionStats_SuccessfulExtractions",
            _("Extraction: SuccessfulExtractions"),
        )
        ExtractionStats_ExtractionConversionsDenied = (
            "ExtractionStats_ExtractionConversionsDenied",
            _("Extraction: ExtractionConversionsDenied"),
        )
        ExtractionStats_ExtractionConversionsCompleted = (
            "ExtractionStats_ExtractionConversionsCompleted",
            _("Extraction: ExtractionConversionsCompleted"),
        )
        ExtractionStats_ExtractionInitiationsDenied = (
            "ExtractionStats_ExtractionInitiationsDenied",
            _("Extraction: ExtractionInitiationsDenied"),
        )
        ExtractionStats_ExtractionInitiationsCompleted = (
            "ExtractionStats_ExtractionInitiationsCompleted",
            _("Extraction: ExtractionInitiationsCompleted"),
        )
        InfectionStats_AlphasKilled = "InfectionStats_AlphasKilled", _(
            "Infection: AlphasKilled"
        )
        InfectionStats_SpartansInfected = "InfectionStats_SpartansInfected", _(
            "Infection: SpartansInfected"
        )
        InfectionStats_SpartansInfectedAsAlpha = (
            "InfectionStats_SpartansInfectedAsAlpha",
            _("Infection: SpartansInfectedAsAlpha"),
        )
        InfectionStats_KillsAsLastSpartanStanding = (
            "InfectionStats_KillsAsLastSpartanStanding",
            _("Infection: KillsAsLastSpartanStanding"),
        )
        InfectionStats_LastSpartansStandingInfected = (
            "InfectionStats_LastSpartansStandingInfected",
            _("Infection: LastSpartansStandingInfected"),
        )
        InfectionStats_RoundsAsAlpha = "InfectionStats_RoundsAsAlpha", _(
            "Infection: RoundsAsAlpha"
        )
        InfectionStats_RoundsAsLastSpartanStanding = (
            "InfectionStats_RoundsAsLastSpartanStanding",
            _("Infection: RoundsAsLastSpartanStanding"),
        )
        InfectionStats_RoundsFinishedAsInfected = (
            "InfectionStats_RoundsFinishedAsInfected",
            _("Infection: RoundsFinishedAsInfected"),
        )
        InfectionStats_RoundsSurvivedAsSpartan = (
            "InfectionStats_RoundsSurvivedAsSpartan",
            _("Infection: RoundsSurvivedAsSpartan"),
        )
        InfectionStats_RoundsSurvivedAsLastSpartanStanding = (
            "InfectionStats_RoundsSurvivedAsLastSpartanStanding",
            _("Infection: RoundsSurvivedAsLastSpartanStanding"),
        )
        InfectionStats_InfectedKilled = "InfectionStats_InfectedKilled", _(
            "Infection: InfectedKilled"
        )
        OddballStats_KillsAsSkullCarrier = "OddballStats_KillsAsSkullCarrier", _(
            "Oddball: KillsAsSkullCarrier"
        )
        OddballStats_SkullCarriersKilled = "OddballStats_SkullCarriersKilled", _(
            "Oddball: SkullCarriersKilled"
        )
        OddballStats_SkullGrabs = "OddballStats_SkullGrabs", _("Oddball: SkullGrabs")
        OddballStats_SkullScoringTicks = "OddballStats_SkullScoringTicks", _(
            "Oddball: SkullScoringTicks"
        )
        ZonesStats_ZoneCaptures = "ZonesStats_ZoneCaptures", _("Zones: ZoneCaptures")
        ZonesStats_ZoneDefensiveKills = "ZonesStats_ZoneDefensiveKills", _(
            "Zones: ZoneDefensiveKills"
        )
        ZonesStats_ZoneOffensiveKills = "ZonesStats_ZoneOffensiveKills", _(
            "Zones: ZoneOffensiveKills"
        )
        ZonesStats_ZoneSecures = "ZonesStats_ZoneSecures", _("Zones: ZoneSecures")
        ZonesStats_ZoneScoringTicks = "ZonesStats_ZoneScoringTicks", _(
            "Zones: ZoneScoringTicks"
        )
        StockpileStats_KillsAsPowerSeedCarrier = (
            "StockpileStats_KillsAsPowerSeedCarrier",
            _("Stockpile: KillsAsPowerSeedCarrier"),
        )
        StockpileStats_PowerSeedCarriersKilled = (
            "StockpileStats_PowerSeedCarriersKilled",
            _("Stockpile: PowerSeedCarriersKilled"),
        )
        StockpileStats_PowerSeedsDeposited = "StockpileStats_PowerSeedsDeposited", _(
            "Stockpile: PowerSeedsDeposited"
        )
        StockpileStats_PowerSeedsStolen = "StockpileStats_PowerSeedsStolen", _(
            "Stockpile: PowerSeedsStolen"
        )

    name = models.CharField(max_length=128, verbose_name="Name")
    description = models.CharField(max_length=256, verbose_name="Description")
    playlist = models.ForeignKey(
        HaloInfinitePlaylist,
        on_delete=models.RESTRICT,
        related_name="domains",
        verbose_name="Playlist",
        blank=True,
        null=True,
    )
    stat = models.CharField(max_length=128, choices=Stats.choices, verbose_name="Stat")
    medal_id = models.IntegerField(
        verbose_name="Medal ID (only necessary if Stat is 'Medal Count')",
        blank=True,
        null=True,
    )
    max_score = models.IntegerField(verbose_name="Max Score")
    effective_date = models.DateField(verbose_name="Effective Date")

    def __str__(self):
        return self.name


class DomainMaster(Base):
    class Meta:
        db_table = "DomainMaster"
        ordering = ["-created_at"]
        verbose_name = "Domain Master"
        verbose_name_plural = "Domain Masters"

    master = models.OneToOneField(
        DiscordAccount, on_delete=models.RESTRICT, related_name="domain_master"
    )
    mastered_at = models.DateTimeField()
    domain_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.master} ({self.mastered_at})"
