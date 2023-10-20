import datetime
from unittest.mock import patch

import pytz
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.season_05.models import Domain, DomainMaster
from apps.season_05.utils import get_active_domains, get_domain_score_info, score_domain


class Season05TestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_domain_master_save(self):
        # Creating a DomainMaster record should be successful
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="test", discord_username="ABC1234"
        )
        domain_master = DomainMaster.objects.create(
            creator=self.user,
            master=discord_account,
            mastered_at=datetime.datetime(
                2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
        self.assertEqual(domain_master.creator, self.user)
        self.assertEqual(domain_master.master_id, discord_account.discord_id)
        self.assertEqual(
            domain_master.mastered_at,
            datetime.datetime(2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(discord_account.domain_master, domain_master)

        # Duplicate DomainMaster record (same `master`) should fail to save
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "DomainMaster_master_id_key"\n'
            + "DETAIL:  Key (master_id)=(test) already exists.\n",
            DomainMaster.objects.create,
            creator=self.user,
            master=discord_account,
            mastered_at=datetime.datetime(
                2023, 7, 7, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )


class UtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.season_05.utils.get_current_time")
    def test_get_active_domains(self, mock_get_current_time):
        mock_get_current_time.return_value = pytz.timezone("America/Denver").localize(
            datetime.datetime(2023, 10, 25, 11, 0, 0, 0)
        )

        # Active Domains is empty to start
        self.assertEqual(len(get_active_domains()), 0)

        # Add a Domain with effective date in the future
        Domain.objects.create(
            creator=self.user,
            name="1name",
            description="1desc",
            stat=Domain.Stats.CoreStats_Kills,
            max_score=1,
            effective_date=datetime.date(year=2023, month=10, day=26),
        )
        self.assertEqual(len(get_active_domains()), 0)

        # Add a Domain with effective date in the past
        Domain.objects.create(
            creator=self.user,
            name="2name",
            description="2desc",
            stat=Domain.Stats.CoreStats_Kills,
            max_score=2,
            effective_date=datetime.date(year=2023, month=10, day=24),
        )
        self.assertEqual(len(get_active_domains()), 1)

        # Add a Domain with effective date today
        Domain.objects.create(
            creator=self.user,
            name="2name",
            description="2desc",
            stat=Domain.Stats.CoreStats_Kills,
            max_score=2,
            effective_date=datetime.date(year=2023, month=10, day=25),
        )

        # Now is past 11AM Mountain
        mock_get_current_time.return_value = pytz.timezone("America/Denver").localize(
            datetime.datetime(2023, 10, 25, 11, 0, 0, 1)
        )
        self.assertEqual(len(get_active_domains()), 2)

        # Now is before 11AM Mountain
        mock_get_current_time.return_value = pytz.timezone("America/Denver").localize(
            datetime.datetime(2023, 10, 25, 10, 59, 59, 999)
        )
        self.assertEqual(len(get_active_domains()), 1)

    def test_score_domain(self):
        all_domain_stats = [
            attr
            for attr in dir(Domain.Stats)
            if attr[:2] + attr[-2:] != "____"
            and not callable(getattr(Domain.Stats, attr))
        ]
        service_record_data_by_playlist = {
            None: {
                "Csr/Seasons/CsrSeason5-1.json": {
                    "MatchesCompleted": 21,
                    "Wins": 13,
                    "Losses": 7,
                    "Ties": 1,
                    "CoreStats": {
                        "Score": 302,
                        "PersonalScore": 45375,
                        "RoundsWon": 15,
                        "RoundsLost": 8,
                        "RoundsTied": 1,
                        "Kills": 349,
                        "Deaths": 241,
                        "Assists": 124,
                        "Suicides": 3,
                        "Betrayals": 1,
                        "GrenadeKills": 22,
                        "HeadshotKills": 242,
                        "MeleeKills": 31,
                        "PowerWeaponKills": 25,
                        "ShotsFired": 5422,
                        "ShotsHit": 2949,
                        "DamageDealt": 104336,
                        "DamageTaken": 85686,
                        "CalloutAssists": 5,
                        "VehicleDestroys": 3,
                        "DriverAssists": 4,
                        "Hijacks": 1,
                        "EmpAssists": 2,
                        "MaxKillingSpree": 10,
                        "Medals": [
                            {
                                "NameId": 1512363953,
                                "Count": 24,
                                "TotalPersonalScoreAwarded": 0,
                            }
                        ],
                    },
                    "CaptureTheFlagStats": {
                        "FlagCaptureAssists": 345,
                        "FlagCaptures": 183,
                        "FlagCarriersKilled": 1982,
                        "FlagGrabs": 2374,
                        "FlagReturnersKilled": 672,
                        "FlagReturns": 318,
                        "FlagSecures": 1285,
                        "FlagSteals": 1168,
                        "KillsAsFlagCarrier": 16,
                        "KillsAsFlagReturner": 160,
                    },
                    "EliminationStats": {
                        "AlliesRevived": 33,
                        "EliminationAssists": 374,
                        "Eliminations": 1920,
                        "EnemyRevivesDenied": 17,
                        "Executions": 43,
                        "KillsAsLastPlayerStanding": 212,
                        "LastPlayersStandingKilled": 314,
                        "RoundsSurvived": 598,
                        "TimesRevivedByAlly": 69,
                    },
                    "ExtractionStats": {
                        "SuccessfulExtractions": 45,
                        "ExtractionConversionsDenied": 12,
                        "ExtractionConversionsCompleted": 14,
                        "ExtractionInitiationsDenied": 36,
                        "ExtractionInitiationsCompleted": 6,
                    },
                    "InfectionStats": {
                        "AlphasKilled": 1018,
                        "SpartansInfected": 744,
                        "SpartansInfectedAsAlpha": 436,
                        "KillsAsLastSpartanStanding": 808,
                        "LastSpartansStandingInfected": 63,
                        "RoundsAsAlpha": 93,
                        "RoundsAsLastSpartanStanding": 114,
                        "RoundsFinishedAsInfected": 775,
                        "RoundsSurvivedAsSpartan": 99,
                        "RoundsSurvivedAsLastSpartanStanding": 37,
                        "InfectedKilled": 3022,
                    },
                    "OddballStats": {
                        "KillsAsSkullCarrier": 1,
                        "SkullCarriersKilled": 9,
                        "SkullGrabs": 3,
                        "SkullScoringTicks": 160,
                    },
                    "ZonesStats": {
                        "ZoneCaptures": 17,
                        "ZoneDefensiveKills": 11,
                        "ZoneOffensiveKills": 21,
                        "ZoneSecures": 1,
                        "ZoneScoringTicks": 212,
                    },
                    "StockpileStats": {
                        "KillsAsPowerSeedCarrier": 1,
                        "PowerSeedCarriersKilled": 1185,
                        "PowerSeedsDeposited": 89,
                        "PowerSeedsStolen": 13,
                    },
                },
                "Csr/Seasons/CsrSeason5-2.json": {
                    "MatchesCompleted": 21,
                    "Wins": 13,
                    "Losses": 7,
                    "Ties": 1,
                    "CoreStats": {
                        "Score": 302,
                        "PersonalScore": 45375,
                        "RoundsWon": 15,
                        "RoundsLost": 8,
                        "RoundsTied": 1,
                        "Kills": 349,
                        "Deaths": 241,
                        "Assists": 124,
                        "Suicides": 3,
                        "Betrayals": 1,
                        "GrenadeKills": 22,
                        "HeadshotKills": 242,
                        "MeleeKills": 31,
                        "PowerWeaponKills": 25,
                        "ShotsFired": 5422,
                        "ShotsHit": 2949,
                        "DamageDealt": 104336,
                        "DamageTaken": 85686,
                        "CalloutAssists": 5,
                        "VehicleDestroys": 3,
                        "DriverAssists": 4,
                        "Hijacks": 1,
                        "EmpAssists": 2,
                        "MaxKillingSpree": 10,
                        "Medals": [
                            {
                                "NameId": 1512363953,
                                "Count": 24,
                                "TotalPersonalScoreAwarded": 0,
                            }
                        ],
                    },
                    "CaptureTheFlagStats": {
                        "FlagCaptureAssists": 345,
                        "FlagCaptures": 183,
                        "FlagCarriersKilled": 1982,
                        "FlagGrabs": 2374,
                        "FlagReturnersKilled": 672,
                        "FlagReturns": 318,
                        "FlagSecures": 1285,
                        "FlagSteals": 1168,
                        "KillsAsFlagCarrier": 16,
                        "KillsAsFlagReturner": 160,
                    },
                    "EliminationStats": {
                        "AlliesRevived": 33,
                        "EliminationAssists": 374,
                        "Eliminations": 1920,
                        "EnemyRevivesDenied": 17,
                        "Executions": 43,
                        "KillsAsLastPlayerStanding": 212,
                        "LastPlayersStandingKilled": 314,
                        "RoundsSurvived": 598,
                        "TimesRevivedByAlly": 69,
                    },
                    "ExtractionStats": {
                        "SuccessfulExtractions": 45,
                        "ExtractionConversionsDenied": 12,
                        "ExtractionConversionsCompleted": 14,
                        "ExtractionInitiationsDenied": 36,
                        "ExtractionInitiationsCompleted": 6,
                    },
                    "InfectionStats": {
                        "AlphasKilled": 1018,
                        "SpartansInfected": 744,
                        "SpartansInfectedAsAlpha": 436,
                        "KillsAsLastSpartanStanding": 808,
                        "LastSpartansStandingInfected": 63,
                        "RoundsAsAlpha": 93,
                        "RoundsAsLastSpartanStanding": 114,
                        "RoundsFinishedAsInfected": 775,
                        "RoundsSurvivedAsSpartan": 99,
                        "RoundsSurvivedAsLastSpartanStanding": 37,
                        "InfectedKilled": 3022,
                    },
                    "OddballStats": {
                        "KillsAsSkullCarrier": 1,
                        "SkullCarriersKilled": 9,
                        "SkullGrabs": 3,
                        "SkullScoringTicks": 160,
                    },
                    "ZonesStats": {
                        "ZoneCaptures": 17,
                        "ZoneDefensiveKills": 11,
                        "ZoneOffensiveKills": 21,
                        "ZoneSecures": 1,
                        "ZoneScoringTicks": 212,
                    },
                    "StockpileStats": {
                        "KillsAsPowerSeedCarrier": 1,
                        "PowerSeedCarriersKilled": 1185,
                        "PowerSeedsDeposited": 89,
                        "PowerSeedsStolen": 13,
                    },
                },
                "Csr/Seasons/CsrSeason5-3.json": {
                    "MatchesCompleted": 21,
                    "Wins": 13,
                    "Losses": 7,
                    "Ties": 1,
                    "CoreStats": {
                        "Score": 302,
                        "PersonalScore": 45375,
                        "RoundsWon": 15,
                        "RoundsLost": 8,
                        "RoundsTied": 1,
                        "Kills": 349,
                        "Deaths": 241,
                        "Assists": 124,
                        "Suicides": 3,
                        "Betrayals": 1,
                        "GrenadeKills": 22,
                        "HeadshotKills": 242,
                        "MeleeKills": 31,
                        "PowerWeaponKills": 25,
                        "ShotsFired": 5422,
                        "ShotsHit": 2949,
                        "DamageDealt": 104336,
                        "DamageTaken": 85686,
                        "CalloutAssists": 5,
                        "VehicleDestroys": 3,
                        "DriverAssists": 4,
                        "Hijacks": 1,
                        "EmpAssists": 2,
                        "MaxKillingSpree": 10,
                        "Medals": [
                            {
                                "NameId": 1512363953,
                                "Count": 24,
                                "TotalPersonalScoreAwarded": 0,
                            }
                        ],
                    },
                    "CaptureTheFlagStats": {
                        "FlagCaptureAssists": 345,
                        "FlagCaptures": 183,
                        "FlagCarriersKilled": 1982,
                        "FlagGrabs": 2374,
                        "FlagReturnersKilled": 672,
                        "FlagReturns": 318,
                        "FlagSecures": 1285,
                        "FlagSteals": 1168,
                        "KillsAsFlagCarrier": 16,
                        "KillsAsFlagReturner": 160,
                    },
                    "EliminationStats": {
                        "AlliesRevived": 33,
                        "EliminationAssists": 374,
                        "Eliminations": 1920,
                        "EnemyRevivesDenied": 17,
                        "Executions": 43,
                        "KillsAsLastPlayerStanding": 212,
                        "LastPlayersStandingKilled": 314,
                        "RoundsSurvived": 598,
                        "TimesRevivedByAlly": 69,
                    },
                    "ExtractionStats": {
                        "SuccessfulExtractions": 45,
                        "ExtractionConversionsDenied": 12,
                        "ExtractionConversionsCompleted": 14,
                        "ExtractionInitiationsDenied": 36,
                        "ExtractionInitiationsCompleted": 6,
                    },
                    "InfectionStats": {
                        "AlphasKilled": 1018,
                        "SpartansInfected": 744,
                        "SpartansInfectedAsAlpha": 436,
                        "KillsAsLastSpartanStanding": 808,
                        "LastSpartansStandingInfected": 63,
                        "RoundsAsAlpha": 93,
                        "RoundsAsLastSpartanStanding": 114,
                        "RoundsFinishedAsInfected": 775,
                        "RoundsSurvivedAsSpartan": 99,
                        "RoundsSurvivedAsLastSpartanStanding": 37,
                        "InfectedKilled": 3022,
                    },
                    "OddballStats": {
                        "KillsAsSkullCarrier": 1,
                        "SkullCarriersKilled": 9,
                        "SkullGrabs": 3,
                        "SkullScoringTicks": 160,
                    },
                    "ZonesStats": {
                        "ZoneCaptures": 17,
                        "ZoneDefensiveKills": 11,
                        "ZoneOffensiveKills": 21,
                        "ZoneSecures": 1,
                        "ZoneScoringTicks": 212,
                    },
                    "StockpileStats": {
                        "KillsAsPowerSeedCarrier": 1,
                        "PowerSeedCarriersKilled": 1185,
                        "PowerSeedsDeposited": 89,
                        "PowerSeedsStolen": 13,
                    },
                },
            }
        }
        for stat in all_domain_stats:
            domain = Domain(creator=self.user, stat=stat, max_score=100)
            if stat == "CoreStats_Medals":
                domain.medal_id = 1512363953
            score, mastered = score_domain(domain, service_record_data_by_playlist)
            self.assertNotEqual(score, 0)
            if mastered:
                self.assertEqual(score, 100)

    def test_get_domain_score_info(self):
        # Missing link returns empty array
        self.assertEqual([], get_domain_score_info(None))
