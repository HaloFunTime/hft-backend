from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.trailblazer.models import (
    TrailblazerTuesdayAttendance,
    TrailblazerTuesdayReferral,
    TrailblazerVODReview,
)
from apps.trailblazer.utils import (
    SEASON_3_START_DAY,
    get_scout_qualified,
    get_sherpa_qualified,
)
from apps.xbox_live.models import XboxLiveAccount


class TrailblazerUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.trailblazer.utils.get_csrs")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_get_sherpa_qualified(
        self, mock_get_xuid_and_exact_gamertag, mock_get_csrs
    ):
        # Empty list provided to method returns nothing
        mock_get_csrs.return_value = {"csrs": {}}
        result = get_sherpa_qualified([])
        self.assertEqual(result, [])
        mock_get_csrs.assert_called_once_with(
            [], "edfef3ac-9cbe-4fa2-b949-8f29deafd483"
        )
        mock_get_csrs.reset_mock()

        # Create some test data
        links = []
        for i in range(10):
            mock_get_xuid_and_exact_gamertag.return_value = (i, f"test{i}")
            discord_account = DiscordAccount.objects.create(
                creator=self.user, discord_id=str(i), discord_tag=f"TestTag{i}#1234"
            )
            xbox_live_account = XboxLiveAccount.objects.create(
                creator=self.user, gamertag=f"testGT{i}"
            )
            links.append(
                DiscordXboxLiveLink.objects.create(
                    creator=self.user,
                    discord_account=discord_account,
                    xbox_live_account=xbox_live_account,
                    verified=True,
                )
            )

        # Success - some current reset max CSRs over 1650 in payload
        mock_get_csrs.return_value = {
            "csrs": {
                0: {
                    "current_reset_max_csr": 1433,
                },
                1: {
                    "current_reset_max_csr": 1840,
                },
                2: {
                    "current_reset_max_csr": 1573,
                },
                3: {
                    "current_reset_max_csr": 1222,
                },
                4: {
                    "current_reset_max_csr": 780,
                },
                5: {
                    "current_reset_max_csr": -1,
                },
                6: {
                    "current_reset_max_csr": 1900,
                },
                7: {
                    "current_reset_max_csr": 1650,
                },
                8: {
                    "current_reset_max_csr": 1649,
                },
                9: {
                    "current_reset_max_csr": 1651,
                },
            }
        }
        result = get_sherpa_qualified(links)
        self.assertEqual(result, ["1", "6", "7", "9"])
        mock_get_csrs.assert_called_once_with(
            [link.xbox_live_account_id for link in links],
            "edfef3ac-9cbe-4fa2-b949-8f29deafd483",
        )
        mock_get_csrs.reset_mock()

    @patch("apps.trailblazer.utils.get_xbox_earn_sets")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_get_scout_qualified(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_xbox_earn_sets,
    ):
        # Empty lists provided to method returns nothing
        mock_get_xbox_earn_sets.return_value = (set(), set(), set())
        result = get_scout_qualified([], [])
        self.assertEqual(result, [])

        # Create some test data
        discord_accounts = []
        links = []
        online_warrior_set = set()
        clean_sweep_set = set()
        extermination_set = set()
        for i in range(30):
            discord_account = DiscordAccount.objects.create(
                creator=self.user, discord_id=str(i), discord_tag=f"TestTag{i}#1234"
            )
            discord_accounts.append(discord_account)
            # Half of all accounts should get linked gamertags
            if i % 2 == 0:
                mock_get_xuid_and_exact_gamertag.return_value = (i, f"test{i}")
                xbox_live_account = XboxLiveAccount.objects.create(
                    creator=self.user, gamertag=f"testGT{i}"
                )
                links.append(
                    DiscordXboxLiveLink.objects.create(
                        creator=self.user,
                        discord_account=discord_account,
                        xbox_live_account=xbox_live_account,
                        verified=True,
                    )
                )
            # Every second account gets an attendance
            if i % 2 == 1:
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_account,
                    attendance_date=SEASON_3_START_DAY,
                )
            # Every third account gets an attendance
            if i % 3 == 0:
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_account,
                    attendance_date=SEASON_3_START_DAY,
                )
            # Every fourth account gets an attendance
            if i % 4 == 0:
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_account,
                    attendance_date=SEASON_3_START_DAY,
                )
            # Every fifth account gets a VOD review
            if i % 5 == 0:
                TrailblazerVODReview.objects.create(
                    creator=self.user,
                    submitter_discord=discord_account,
                    submission_date=SEASON_3_START_DAY,
                )
            # Every sixth account gets a VOD review
            if i % 6 == 0:
                TrailblazerVODReview.objects.create(
                    creator=self.user,
                    submitter_discord=discord_account,
                    submission_date=SEASON_3_START_DAY,
                )
            # Every seventh account gets a referral
            if i % 7 == 0:
                TrailblazerTuesdayReferral.objects.create(
                    creator=self.user,
                    referrer_discord=discord_account,
                    invitee_discord=discord_account,
                    referral_date=SEASON_3_START_DAY,
                )
            # Every second account earns online warrior
            if i % 2 == 0:
                online_warrior_set.add(i)
            # Every third account earns clean sweep
            if i % 3 == 0:
                clean_sweep_set.add(i)
            # Every sixth account earns extermination
            if i % 6 == 0:
                extermination_set.add(i)
        mock_get_xbox_earn_sets.return_value = (
            online_warrior_set,
            clean_sweep_set,
            extermination_set,
        )

        # The test data above results in every sixth account clearing the 500 point threshold
        result = get_scout_qualified([da.discord_id for da in discord_accounts], links)
        self.assertEqual(result, ["0", "6", "12", "18", "24"])
