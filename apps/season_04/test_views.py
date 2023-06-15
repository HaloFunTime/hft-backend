import datetime
from unittest.mock import call, patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.fun_time_friday.models import (
    FunTimeFridayVoiceConnect,
    FunTimeFridayVoiceDisconnect,
)
from apps.halo_infinite.constants import (
    GAME_VARIANT_CATEGORY_INFECTION,
    MEDAL_ID_PERFECTION,
    PLAYLIST_ID_BOT_BOOTCAMP,
    SEASON_3_API_ID,
    SEASON_3_START_TIME,
)
from apps.link.models import DiscordXboxLiveLink
from apps.reputation.models import PlusRep
from apps.xbox_live.models import XboxLiveAccount


class Season04TestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_check_stamps_request_errors(self):
        # Missing field values throw errors
        response = self.client.post("/season-04/check-stamps", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("funTimerRank", details)
        self.assertEqual(
            details.get("funTimerRank"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("inviteUses", details)
        self.assertEqual(
            details.get("inviteUses"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("societiesJoined", details)
        self.assertEqual(
            details.get("societiesJoined"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-04/check-stamps",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
                "funTimerRank": -1,
                "inviteUses": -1,
                "societiesJoined": -1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )
        self.assertIn("funTimerRank", details)
        self.assertEqual(
            details.get("funTimerRank")[0],
            ErrorDetail(
                string="Ensure this value is greater than or equal to 0.",
                code="min_value",
            ),
        )
        self.assertIn("inviteUses", details)
        self.assertEqual(
            details.get("inviteUses")[0],
            ErrorDetail(
                string="Ensure this value is greater than or equal to 0.",
                code="min_value",
            ),
        )
        self.assertIn("societiesJoined", details)
        self.assertEqual(
            details.get("societiesJoined")[0],
            ErrorDetail(
                string="Ensure this value is greater than or equal to 0.",
                code="min_value",
            ),
        )

    @patch("apps.season_04.views.get_season_custom_matches_for_xuid")
    @patch("apps.season_04.views.service_record")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_check_stamps_view(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_service_record,
        mock_get_season_custom_matches_for_xuid,
    ):
        # Create test data
        season_start_time = SEASON_3_START_TIME
        season_api_id = SEASON_3_API_ID
        season_id = "3"
        mock_get_xuid_and_exact_gamertag.return_value = (4567, "test1234")
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="1234", discord_username="TestUsername1234"
        )
        xbox_live_account = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="testGT1234"
        )
        link = DiscordXboxLiveLink.objects.create(
            creator=self.user,
            discord_account=discord_account,
            xbox_live_account=xbox_live_account,
            verified=True,
        )
        plus_reps = []
        for _ in range(3):
            plus_reps.append(
                PlusRep.objects.create(
                    creator=self.user,
                    giver=discord_account,
                    receiver=discord_account,
                )
            )
        FunTimeFridayVoiceConnect.objects.create(
            creator=self.user,
            connector_discord=discord_account,
            connected_at=season_start_time,
            channel_id="test123",
        )
        FunTimeFridayVoiceDisconnect.objects.create(
            creator=self.user,
            disconnector_discord=discord_account,
            disconnected_at=season_start_time + datetime.timedelta(hours=4),
            channel_id="test123",
        )

        # Success - point totals come through for all values
        mock_service_record.side_effect = [
            {
                "Wins": 6,
                "CoreStats": {
                    "Kills": 7,
                    "HeadshotKills": 8,
                    "PowerWeaponKills": 9,
                },
            },
            {
                "CoreStats": {
                    "Medals": [
                        {
                            "NameId": MEDAL_ID_PERFECTION,
                            "Count": 10,
                        }
                    ],
                }
            },
        ]
        mock_get_season_custom_matches_for_xuid.return_value = [
            {
                "MatchInfo": {
                    "StartTime": "2023-06-01T00:00:00.000Z",
                    "EndTime": "2023-06-01T01:06:00.000Z",
                    "GameVariantCategory": 15,
                    "MapVariant": {
                        "AssetId": "test01",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test01",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-02T00:00:00.000Z",
                    "EndTime": "2023-06-02T01:06:00.000Z",
                    "GameVariantCategory": GAME_VARIANT_CATEGORY_INFECTION,
                    "MapVariant": {
                        "AssetId": "test02",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test02",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-03T00:00:00.000Z",
                    "EndTime": "2023-06-03T01:06:00.000Z",
                    "GameVariantCategory": 15,
                    "MapVariant": {
                        "AssetId": "test03",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test03",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-04T00:00:00.000Z",
                    "EndTime": "2023-06-04T01:06:00.000Z",
                    "GameVariantCategory": GAME_VARIANT_CATEGORY_INFECTION,
                    "MapVariant": {
                        "AssetId": "test04",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test04",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-05T00:00:00.000Z",
                    "EndTime": "2023-06-05T01:06:00.000Z",
                    "GameVariantCategory": 15,
                    "MapVariant": {
                        "AssetId": "test05",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test05",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-06T00:00:00.000Z",
                    "EndTime": "2023-06-06T01:06:00.000Z",
                    "GameVariantCategory": GAME_VARIANT_CATEGORY_INFECTION,
                    "MapVariant": {
                        "AssetId": "test06",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test06",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-07T00:00:00.000Z",
                    "EndTime": "2023-06-07T01:06:00.000Z",
                    "GameVariantCategory": 15,
                    "MapVariant": {
                        "AssetId": "test07",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test07",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-08T00:00:00.000Z",
                    "EndTime": "2023-06-08T01:06:00.000Z",
                    "GameVariantCategory": GAME_VARIANT_CATEGORY_INFECTION,
                    "MapVariant": {
                        "AssetId": "test08",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test08",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-09T00:00:00.000Z",
                    "EndTime": "2023-06-09T01:06:00.000Z",
                    "GameVariantCategory": 15,
                    "MapVariant": {
                        "AssetId": "test09",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test09",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-10T00:00:00.000Z",
                    "EndTime": "2023-06-10T01:06:00.000Z",
                    "GameVariantCategory": GAME_VARIANT_CATEGORY_INFECTION,
                    "MapVariant": {
                        "AssetId": "test10",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test10",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-11T00:00:00.000Z",
                    "EndTime": "2023-06-11T01:06:00.000Z",
                    "GameVariantCategory": 15,
                    "MapVariant": {
                        "AssetId": "test11",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test11",
                    },
                },
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-11T00:00:00.000Z",
                    "EndTime": "2023-06-11T00:00:00.000Z",
                    "GameVariantCategory": 15,
                    "MapVariant": {
                        "AssetId": "test12",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test12",
                    },
                },
                "PresentAtEndOfMatch": False,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-11T00:00:00.000Z",
                    "EndTime": "2023-06-11T00:00:00.000Z",
                    "GameVariantCategory": 15,
                    "MapVariant": {
                        "AssetId": "test13",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test13",
                    },
                },
                "PresentAtEndOfMatch": False,
            },
            {
                "MatchInfo": {
                    "StartTime": "2023-06-11T00:00:00.000Z",
                    "EndTime": "2023-06-11T00:00:00.000Z",
                    "GameVariantCategory": 15,
                    "MapVariant": {
                        "AssetId": "test13",
                    },
                    "UgcGameVariant": {
                        "AssetId": "test14",
                    },
                },
                "PresentAtEndOfMatch": False,
            },
        ]
        response = self.client.post(
            "/season-04/check-stamps",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
                "funTimerRank": 1,
                "inviteUses": 2,
                "societiesJoined": 5,
            },
            format="json",
        )
        mock_service_record.assert_has_calls(
            [
                call(link.xbox_live_account_id, season_api_id),
                call(
                    link.xbox_live_account_id, season_api_id, PLAYLIST_ID_BOT_BOOTCAMP
                ),
            ]
        )
        mock_get_season_custom_matches_for_xuid.assert_called_once_with(
            link.xbox_live_account_id, season_id
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("discordUserId"), link.discord_account_id)
        self.assertEqual(response.data.get("stampsCompleted"), 4)
        self.assertEqual(response.data.get("scoreChatterbox"), 1)
        self.assertEqual(response.data.get("scoreFuntagious"), 2)
        self.assertEqual(response.data.get("scoreReppingIt"), 3)
        self.assertEqual(response.data.get("scoreFundurance"), 4)
        self.assertEqual(response.data.get("scoreSecretSocialite"), 5)
        self.assertEqual(response.data.get("scoreStackingDubs"), 6)
        self.assertEqual(response.data.get("scoreLicenseToKill"), 7)
        self.assertEqual(response.data.get("scoreAimForTheHead"), 8)
        self.assertEqual(response.data.get("scorePowerTrip"), 9)
        self.assertEqual(response.data.get("scoreBotBullying"), 10)
        self.assertEqual(response.data.get("scoreOneFundo"), 11)
        self.assertEqual(response.data.get("scoreGleeFiddy"), 12)
        self.assertEqual(response.data.get("scoreWellTraveled"), 13)
        self.assertEqual(response.data.get("scoreMoModesMoFun"), 14)
        self.assertEqual(response.data.get("scoreEpidemic"), 5)
        self.assertEqual(response.data.get("completedFinishInFive"), False)
        self.assertEqual(response.data.get("completedVictoryLap"), False)
        self.assertEqual(response.data.get("completedTypeA"), False)
        self.assertEqual(response.data.get("completedFormerlyChucks"), False)
        self.assertEqual(response.data.get("completedInParticular"), False)
        mock_service_record.reset_mock()
        mock_get_season_custom_matches_for_xuid.reset_mock()

        # Success - no linked gamertag
        link.delete()
        response = self.client.post(
            "/season-04/check-stamps",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
                "funTimerRank": 1,
                "inviteUses": 2,
                "societiesJoined": 5,
            },
            format="json",
        )
        mock_service_record.assert_not_called()
        mock_get_season_custom_matches_for_xuid.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("discordUserId"), link.discord_account_id)
        self.assertEqual(response.data.get("stampsCompleted"), 3)
        self.assertEqual(response.data.get("scoreChatterbox"), 1)
        self.assertEqual(response.data.get("scoreFuntagious"), 2)
        self.assertEqual(response.data.get("scoreReppingIt"), 3)
        self.assertEqual(response.data.get("scoreFundurance"), 4)
        self.assertEqual(response.data.get("scoreSecretSocialite"), 5)
        self.assertEqual(response.data.get("scoreStackingDubs"), 0)
        self.assertEqual(response.data.get("scoreLicenseToKill"), 0)
        self.assertEqual(response.data.get("scoreAimForTheHead"), 0)
        self.assertEqual(response.data.get("scorePowerTrip"), 0)
        self.assertEqual(response.data.get("scoreBotBullying"), 0)
        self.assertEqual(response.data.get("scoreOneFundo"), 0)
        self.assertEqual(response.data.get("scoreGleeFiddy"), 0)
        self.assertEqual(response.data.get("scoreWellTraveled"), 0)
        self.assertEqual(response.data.get("scoreMoModesMoFun"), 0)
        self.assertEqual(response.data.get("scoreEpidemic"), 0)
        self.assertEqual(response.data.get("completedFinishInFive"), False)
        self.assertEqual(response.data.get("completedVictoryLap"), False)
        self.assertEqual(response.data.get("completedTypeA"), False)
        self.assertEqual(response.data.get("completedFormerlyChucks"), False)
        self.assertEqual(response.data.get("completedInParticular"), False)
