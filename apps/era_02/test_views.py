import datetime
import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.era_02.models import MVT, TeamUpChallengeCompletion, TeamUpChallenges
from apps.halo_infinite.models import HaloInfiniteMatch
from apps.link.models import DiscordXboxLiveLink
from apps.xbox_live.models import XboxLiveAccount


class Era02TestCase(APITestCase):
    @patch("apps.halo_infinite.signals.match_stats")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def setUp(self, mock_get_xuid_and_exact_gamertag, mock_match_stats):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)
        # Create a DiscordAccount with a linked gamertag
        self.discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="1234", discord_username="Test1234"
        )
        mock_get_xuid_and_exact_gamertag.return_value = (1234, "test1234")
        self.xbl_account = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="test1234"
        )
        self.link = DiscordXboxLiveLink.objects.create(
            creator=self.user,
            discord_account=self.discord_account,
            xbox_live_account=self.xbl_account,
            verified=True,
        )
        # Create a HaloInfiniteMatch
        self.match_id = uuid.uuid4()
        mock_match_stats.return_value = {
            "MatchId": str(self.match_id),
            "MatchInfo": {
                "StartTime": "2023-01-02T07:50:24.936Z",
                "EndTime": "2023-01-02T08:06:04.702Z",
            },
        }
        self.match = HaloInfiniteMatch.objects.create(
            creator=self.user, match_id=self.match_id
        )

    def test_save_mvt_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-02/save-mvt", {}, format="json")
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
        self.assertIn("mvtPoints", details)
        self.assertEqual(
            details.get("mvtPoints"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-02/save-mvt",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
                "mvtPoints": "not_an_int",
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
        self.assertIn("mvtPoints", details)
        self.assertEqual(
            details.get("mvtPoints")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )

        # New MVT
        now_before_post = datetime.datetime.now(tz=datetime.timezone.utc)
        response = self.client.post(
            "/era-02/save-mvt",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
                "mvtPoints": 100,
            },
            format="json",
        )
        self.assertEqual(MVT.objects.all().count(), 1)
        mvt_record = MVT.objects.first()
        self.assertEqual(mvt_record.earner_id, "123")
        self.assertGreaterEqual(mvt_record.earned_at, now_before_post)
        self.assertEqual(mvt_record.mvt_points, 100)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMVT"), True)
        self.assertEqual(response.data.get("maxed"), False)
        initial_earned_at = mvt_record.earned_at

        # Existing MVT, MVT points update
        response = self.client.post(
            "/era-02/save-mvt",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "mvtPoints": 117,
            },
            format="json",
        )
        self.assertEqual(MVT.objects.all().count(), 1)
        mvt_record = MVT.objects.first()
        self.assertEqual(mvt_record.earner_id, "123")
        self.assertGreaterEqual(mvt_record.earned_at, initial_earned_at)
        self.assertEqual(mvt_record.mvt_points, 117)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMVT"), False)
        self.assertEqual(response.data.get("maxed"), False)

        # Existing MVT, maxed
        response = self.client.post(
            "/era-02/save-mvt",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "mvtPoints": 250,
            },
            format="json",
        )
        self.assertEqual(MVT.objects.all().count(), 1)
        mvt_record = MVT.objects.first()
        self.assertEqual(mvt_record.earner_id, "123")
        self.assertGreaterEqual(mvt_record.earned_at, initial_earned_at)
        self.assertEqual(mvt_record.mvt_points, 250)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMVT"), False)
        self.assertEqual(response.data.get("maxed"), True)

    def test_check_player_games_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-02/check-player-games", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-02/check-player-games",
            {
                "discordUserId": ["abc"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Not a valid string.", code="invalid"),
        )

        # TODO: Test the rest... or not

    def test_check_team_up_challenges_view(self):
        # Missing field values throw errors
        response = self.client.post(
            "/era-02/check-team-up-challenges", {}, format="json"
        )
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

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-02/check-team-up-challenges",
            {
                "discordUserId": ["abc"],
                "discordUsername": ["abc"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Not a valid string.", code="invalid"),
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername")[0],
            ErrorDetail(string="Not a valid string.", code="invalid"),
        )

        # Zeroes are returned successfully with no completions in the system
        response = self.client.post(
            "/era-02/check-team-up-challenges",
            {
                "discordUserId": self.discord_account.discord_id,
                "discordUsername": self.discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data.get("discordUserId"), self.discord_account.discord_id
        )
        self.assertTrue(response.data.get("linkedGamertag"))
        self.assertEqual(response.data.get("completionsBaitTheFlags"), 0)
        self.assertEqual(response.data.get("completionsFortyFists"), 0)
        self.assertEqual(response.data.get("completionsGrenadeParade"), 0)
        self.assertEqual(response.data.get("completionsHundredHeads"), 0)
        self.assertEqual(response.data.get("completionsMostValuableDriver"), 0)
        self.assertEqual(response.data.get("completionsOwnTheZones"), 0)
        self.assertEqual(response.data.get("completionsSpeedForSeeds"), 0)
        self.assertEqual(response.data.get("completionsSpinClass"), 0)
        self.assertEqual(response.data.get("completionsStickyIcky"), 0)
        self.assertEqual(response.data.get("completionsSummonADemon"), 0)

        # Completions are returned successfully if present
        n = 0
        for challenge in [
            TeamUpChallenges.BAIT_THE_FLAGS,
            TeamUpChallenges.FORTY_FISTS,
            TeamUpChallenges.GRENADE_PARADE,
            TeamUpChallenges.HUNDRED_HEADS,
            TeamUpChallenges.MOST_VALUABLE_DRIVER,
            TeamUpChallenges.OWN_THE_ZONES,
            TeamUpChallenges.SPEED_FOR_SEEDS,
            TeamUpChallenges.SPIN_CLASS,
            TeamUpChallenges.STICKY_ICKY,
            TeamUpChallenges.SUMMON_A_DEMON,
        ]:
            n += 1
            for _ in range(n):
                TeamUpChallengeCompletion.objects.create(
                    creator=self.user,
                    xuid=self.xbl_account.xuid,
                    challenge=challenge,
                    match=self.match,
                )
        response = self.client.post(
            "/era-02/check-team-up-challenges",
            {
                "discordUserId": self.discord_account.discord_id,
                "discordUsername": self.discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data.get("discordUserId"), self.discord_account.discord_id
        )
        self.assertTrue(response.data.get("linkedGamertag"))
        self.assertEqual(response.data.get("completionsBaitTheFlags"), 1)
        self.assertEqual(response.data.get("completionsFortyFists"), 2)
        self.assertEqual(response.data.get("completionsGrenadeParade"), 3)
        self.assertEqual(response.data.get("completionsHundredHeads"), 4)
        self.assertEqual(response.data.get("completionsMostValuableDriver"), 5)
        self.assertEqual(response.data.get("completionsOwnTheZones"), 6)
        self.assertEqual(response.data.get("completionsSpeedForSeeds"), 7)
        self.assertEqual(response.data.get("completionsSpinClass"), 8)
        self.assertEqual(response.data.get("completionsStickyIcky"), 9)
        self.assertEqual(response.data.get("completionsSummonADemon"), 10)

        # Zeroes are returned with no link record
        self.link.delete()
        response = self.client.post(
            "/era-02/check-team-up-challenges",
            {
                "discordUserId": self.discord_account.discord_id,
                "discordUsername": self.discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data.get("discordUserId"), self.discord_account.discord_id
        )
        self.assertFalse(response.data.get("linkedGamertag"))
        self.assertEqual(response.data.get("completionsBaitTheFlags"), 0)
        self.assertEqual(response.data.get("completionsFortyFists"), 0)
        self.assertEqual(response.data.get("completionsGrenadeParade"), 0)
        self.assertEqual(response.data.get("completionsHundredHeads"), 0)
        self.assertEqual(response.data.get("completionsMostValuableDriver"), 0)
        self.assertEqual(response.data.get("completionsOwnTheZones"), 0)
        self.assertEqual(response.data.get("completionsSpeedForSeeds"), 0)
        self.assertEqual(response.data.get("completionsSpinClass"), 0)
        self.assertEqual(response.data.get("completionsStickyIcky"), 0)
        self.assertEqual(response.data.get("completionsSummonADemon"), 0)
