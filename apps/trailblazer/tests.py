import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.halo_infinite.utils import SEASON_3_START_TIME, SEASON_4_START_TIME
from apps.link.models import DiscordXboxLiveLink
from apps.trailblazer.models import (
    TrailblazerExcellentVODReview,
    TrailblazerTuesdayAttendance,
    TrailblazerTuesdayReferral,
    TrailblazerVODSubmission,
)
from apps.trailblazer.utils import (
    get_s3_discord_earn_dict,
    get_s4_discord_earn_dict,
    is_s3_scout_qualified,
    is_s4_scout_qualified,
    is_scout_qualified,
    is_sherpa_qualified,
)
from apps.xbox_live.models import XboxLiveAccount


class TrailblazerUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_get_s3_discord_earn_dict(self):
        # Create some test data
        discord_accounts = []
        for i in range(2):
            discord_accounts.append(
                DiscordAccount.objects.create(
                    creator=self.user,
                    discord_id=str(i),
                    discord_username=f"TestUsername{i}",
                )
            )

        # No IDs = No earn dicts
        earn_dict = get_s3_discord_earn_dict([])
        self.assertEqual(earn_dict, {})

        # Max Points - exactly
        cotcs = []
        for i in range(5):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 4, 6),
                )
            )
        sics = []
        for i in range(3):
            sics.append(
                TrailblazerTuesdayReferral.objects.create(
                    creator=self.user,
                    referrer_discord=discord_accounts[0],
                    invitee_discord=discord_accounts[1],
                    referral_date=datetime.date(2023, 4, 6),
                )
            )
        bs = []
        for i in range(2):
            bs.append(
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_accounts[0],
                    submission_date=datetime.date(2023, 4, 6),
                )
            )
        earn_dict = get_s3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 250
        )
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["sharing_is_caring"], 150
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bookworm"], 100)

        # Max points - overages
        for i in range(2):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 4, 6),
                )
            )
            sics.append(
                TrailblazerTuesdayReferral.objects.create(
                    creator=self.user,
                    referrer_discord=discord_accounts[0],
                    invitee_discord=discord_accounts[1],
                    referral_date=datetime.date(2023, 4, 6),
                )
            )
            bs.append(
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_accounts[0],
                    submission_date=datetime.date(2023, 4, 6),
                )
            )
        earn_dict = get_s3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 250
        )
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["sharing_is_caring"], 150
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bookworm"], 100)

        # Deletion of all records eliminates points
        for cotc in cotcs:
            cotc.delete()
        for sic in sics:
            sic.delete()
        for b in bs:
            b.delete()
        earn_dict = get_s3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 0
        )
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["sharing_is_caring"], 0
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bookworm"], 0)

        # Addition of records outside the date range still results in no points
        cotcs = []
        for i in range(5):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 7, 6),
                )
            )
        sics = []
        for i in range(3):
            sics.append(
                TrailblazerTuesdayReferral.objects.create(
                    creator=self.user,
                    referrer_discord=discord_accounts[0],
                    invitee_discord=discord_accounts[1],
                    referral_date=datetime.date(2023, 7, 6),
                )
            )
        bs = []
        for i in range(2):
            bs.append(
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_accounts[0],
                    submission_date=datetime.date(2023, 7, 6),
                )
            )
        earn_dict = get_s3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 0
        )
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["sharing_is_caring"], 0
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bookworm"], 0)

    @patch("apps.trailblazer.utils.get_s3_xbox_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_is_s3_scout_qualified(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s3_xbox_earn_dict,
    ):
        # Null value provided to method returns False
        mock_get_s3_xbox_earn_dict.return_value = {}
        result = is_s3_scout_qualified(None, None)
        self.assertEqual(result, False)

        # Create some test data
        discord_accounts = []
        link_for_discord_account = {}
        xbox_earn_dict = {}
        for i in range(30):
            discord_account = DiscordAccount.objects.create(
                creator=self.user,
                discord_id=str(i),
                discord_username=f"TestUsername{i}",
            )
            discord_accounts.append(discord_account)
            # Half of all accounts should get linked gamertags
            if i % 2 == 0:
                mock_get_xuid_and_exact_gamertag.return_value = (i, f"test{i}")
                xbox_live_account = XboxLiveAccount.objects.create(
                    creator=self.user, gamertag=f"testGT{i}"
                )
                link_for_discord_account[str(i)] = DiscordXboxLiveLink.objects.create(
                    creator=self.user,
                    discord_account=discord_account,
                    xbox_live_account=xbox_live_account,
                    verified=True,
                )
                xbox_earn_dict[i] = {
                    "online_warrior": 0,
                    "hot_streak": 0,
                    "oddly_effective": 0,
                    "too_stronk": 0,
                }
            # Every second account gets an attendance
            if i % 2 == 1:
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_account,
                    attendance_date=SEASON_3_START_TIME,
                )
            # Every third account gets an attendance
            if i % 3 == 0:
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_account,
                    attendance_date=SEASON_3_START_TIME,
                )
            # Every fourth account gets an attendance
            if i % 4 == 0:
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_account,
                    attendance_date=SEASON_3_START_TIME,
                )
            # Every fifth account gets a VOD review
            if i % 5 == 0:
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_account,
                    submission_date=SEASON_3_START_TIME,
                )
            # Every sixth account gets a VOD review
            if i % 6 == 0:
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_account,
                    submission_date=SEASON_3_START_TIME,
                )
            # Every seventh account gets a referral
            if i % 7 == 0:
                TrailblazerTuesdayReferral.objects.create(
                    creator=self.user,
                    referrer_discord=discord_account,
                    invitee_discord=discord_account,
                    referral_date=SEASON_3_START_TIME,
                )
            # Every second account earns Online Warrior
            if i % 2 == 0 and i in xbox_earn_dict:
                xbox_earn_dict[i]["online_warrior"] = 200
            # Every third account earns Hot Streak
            if i % 3 == 0 and i in xbox_earn_dict:
                xbox_earn_dict[i]["hot_streak"] = 100
            # Every fifth account earns Oddly Effective
            if i % 6 == 0 and i in xbox_earn_dict:
                xbox_earn_dict[i]["oddly_effective"] = 100
            # Every sixth account earns Too Stronk
            if i % 6 == 0 and i in xbox_earn_dict:
                xbox_earn_dict[i]["too_stronk"] = 100
        mock_get_s3_xbox_earn_dict.return_value = xbox_earn_dict

        # The test data above results in every sixth account clearing the 500 point threshold
        scout_qualified_discord_ids = {"0", "6", "12", "18", "24"}
        for i in range(30):
            discord_id = str(i)
            link = link_for_discord_account.get(discord_id)
            xuid = None if link is None else link.xbox_live_account_id
            result = is_s3_scout_qualified(discord_id, xuid)
            self.assertEqual(result, discord_id in scout_qualified_discord_ids)

    def test_get_s4_discord_earn_dict(self):
        # Create some test data
        discord_accounts = []
        for i in range(2):
            discord_accounts.append(
                DiscordAccount.objects.create(
                    creator=self.user,
                    discord_id=str(i),
                    discord_username=f"TestUsername{i}",
                )
            )

        # No IDs = No earn dicts
        earn_dict = get_s4_discord_earn_dict([])
        self.assertEqual(earn_dict, {})

        # Max Points - exactly
        cotcs = []
        for i in range(5):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 7, 6),
                )
            )
        bs = []
        for i in range(3):
            bs.append(
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_accounts[0],
                    submission_date=datetime.date(2023, 7, 6),
                )
            )
        fcs = []
        fcs.append(
            TrailblazerExcellentVODReview.objects.create(
                creator=self.user,
                reviewer_discord=discord_accounts[0],
                review_date=datetime.date(2023, 7, 6),
            )
        )
        earn_dict = get_s4_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 250
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bookworm"], 150)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["film_critic"], 100)

        # Max points - overages
        for i in range(2):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 7, 6),
                )
            )
            fcs.append(
                TrailblazerExcellentVODReview.objects.create(
                    creator=self.user,
                    reviewer_discord=discord_accounts[0],
                    review_date=datetime.date(2023, 7, 6),
                )
            )
            bs.append(
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_accounts[0],
                    submission_date=datetime.date(2023, 7, 6),
                )
            )
        earn_dict = get_s4_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 250
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bookworm"], 150)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["film_critic"], 100)

        # Deletion of all records eliminates points
        for cotc in cotcs:
            cotc.delete()
        for fc in fcs:
            fc.delete()
        for b in bs:
            b.delete()
        earn_dict = get_s4_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 0
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bookworm"], 0)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["film_critic"], 0)

        # Addition of records outside the date range still results in no points
        cotcs = []
        for i in range(5):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 4, 6),
                )
            )
        fcs = []
        fcs.append(
            TrailblazerExcellentVODReview.objects.create(
                creator=self.user,
                reviewer_discord=discord_accounts[0],
                review_date=datetime.date(2023, 4, 6),
            )
        )
        bs = []
        for i in range(3):
            bs.append(
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_accounts[0],
                    submission_date=datetime.date(2023, 4, 6),
                )
            )
        earn_dict = get_s4_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 0
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bookworm"], 0)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["film_critic"], 0)

    @patch("apps.trailblazer.utils.get_s4_xbox_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_is_s4_scout_qualified(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s4_xbox_earn_dict,
    ):
        # Null value provided to method returns False
        mock_get_s4_xbox_earn_dict.return_value = {}
        result = is_s4_scout_qualified(None, None)
        self.assertEqual(result, False)

        # Create some test data
        discord_accounts = []
        link_for_discord_account = {}
        xbox_earn_dict = {}
        for i in range(30):
            discord_account = DiscordAccount.objects.create(
                creator=self.user,
                discord_id=str(i),
                discord_username=f"TestUsername{i}",
            )
            discord_accounts.append(discord_account)
            # Half of all accounts should get linked gamertags
            if i % 2 == 0:
                mock_get_xuid_and_exact_gamertag.return_value = (i, f"test{i}")
                xbox_live_account = XboxLiveAccount.objects.create(
                    creator=self.user, gamertag=f"testGT{i}"
                )
                link_for_discord_account[str(i)] = DiscordXboxLiveLink.objects.create(
                    creator=self.user,
                    discord_account=discord_account,
                    xbox_live_account=xbox_live_account,
                    verified=True,
                )
                xbox_earn_dict[i] = {
                    "online_warrior": 0,
                    "the_cycle": 0,
                    "checkered_flag": 0,
                    "them_thar_hills": 0,
                }
            # Every second account gets an attendance
            if i % 2 == 1:
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_account,
                    attendance_date=SEASON_4_START_TIME,
                )
            # Every third account gets an attendance
            if i % 3 == 0:
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_account,
                    attendance_date=SEASON_4_START_TIME,
                )
            # Every fourth account gets an attendance
            if i % 4 == 0:
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_account,
                    attendance_date=SEASON_4_START_TIME,
                )
            # Every fifth account gets a VOD review
            if i % 5 == 0:
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_account,
                    submission_date=SEASON_4_START_TIME,
                )
            # Every sixth account gets a VOD review
            if i % 6 == 0:
                TrailblazerVODSubmission.objects.create(
                    creator=self.user,
                    submitter_discord=discord_account,
                    submission_date=SEASON_4_START_TIME,
                )
            # Every seventh account gets an excellent review
            if i % 7 == 0:
                TrailblazerExcellentVODReview.objects.create(
                    creator=self.user,
                    reviewer_discord=discord_account,
                    review_date=SEASON_4_START_TIME,
                )
            # Every second account earns Online Warrior
            if i % 2 == 0 and i in xbox_earn_dict:
                xbox_earn_dict[i]["online_warrior"] = 200
            # Every third account earns The Cycle
            if i % 3 == 0 and i in xbox_earn_dict:
                xbox_earn_dict[i]["the_cycle"] = 100
            # Every fifth account earns Checkered Flag
            if i % 6 == 0 and i in xbox_earn_dict:
                xbox_earn_dict[i]["checkered_flag"] = 100
            # Every sixth account earns Them Thar Hills
            if i % 6 == 0 and i in xbox_earn_dict:
                xbox_earn_dict[i]["them_thar_hills"] = 100
        mock_get_s4_xbox_earn_dict.return_value = xbox_earn_dict

        # The test data above results in every sixth account clearing the 500 point threshold
        scout_qualified_discord_ids = {"0", "6", "12", "18", "24"}
        for i in range(30):
            discord_id = str(i)
            link = link_for_discord_account.get(discord_id)
            xuid = None if link is None else link.xbox_live_account_id
            result = is_s4_scout_qualified(discord_id, xuid)
            self.assertEqual(result, discord_id in scout_qualified_discord_ids)

    @patch("apps.trailblazer.utils.is_s4_scout_qualified")
    @patch("apps.trailblazer.utils.is_s3_scout_qualified")
    @patch("apps.trailblazer.utils.get_current_season_id")
    def test_is_scout_qualified(
        self,
        mock_get_current_season_id,
        mock_is_s3_scout_qualified,
        mock_is_s4_scout_qualified,
    ):
        def reset_all_mocks():
            mock_get_current_season_id.reset_mock()
            mock_is_s3_scout_qualified.reset_mock()
            mock_is_s4_scout_qualified.reset_mock()

        # Season 3
        mock_get_current_season_id.return_value = "3"
        mock_is_s3_scout_qualified.return_value = True
        result = is_scout_qualified("123", 123)
        self.assertEqual(result, True)
        mock_get_current_season_id.assert_called_once_with()
        mock_is_s3_scout_qualified.assert_called_once_with("123", 123)
        mock_is_s4_scout_qualified.assert_not_called()
        reset_all_mocks()

        # Season 4
        mock_get_current_season_id.return_value = "4"
        mock_is_s4_scout_qualified.return_value = True
        result = is_scout_qualified("123", 123)
        self.assertEqual(result, True)
        mock_get_current_season_id.assert_called_once_with()
        mock_is_s3_scout_qualified.assert_not_called()
        mock_is_s4_scout_qualified.assert_called_once_with("123", 123)
        reset_all_mocks()

    @patch("apps.trailblazer.utils.get_csrs")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_is_sherpa_qualified(self, mock_get_xuid_and_exact_gamertag, mock_get_csrs):
        # Null value provided to method returns False
        mock_get_csrs.return_value = {"csrs": {}}
        result = is_sherpa_qualified(None)
        self.assertEqual(result, False)
        mock_get_csrs.assert_called_once_with(
            [None], "edfef3ac-9cbe-4fa2-b949-8f29deafd483"
        )
        mock_get_csrs.reset_mock()

        # Create some test data
        links = []
        for i in range(10):
            mock_get_xuid_and_exact_gamertag.return_value = (i, f"test{i}")
            discord_account = DiscordAccount.objects.create(
                creator=self.user,
                discord_id=str(i),
                discord_username=f"TestUsername{i}",
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

        # Returns appropriate value based on whether current reset max CSRs are >= 1650
        example_csrs = [1433, 1840, 1573, 1222, 780, -1, 1900, 1650, 1649, 1651]
        for i in range(10):
            mock_get_csrs.return_value = {
                "csrs": {
                    i: {
                        "current_reset_max_csr": example_csrs[i],
                    },
                }
            }
            result = is_sherpa_qualified(i)
            self.assertEqual(result, example_csrs[i] >= 1650)
            mock_get_csrs.assert_called_once_with(
                [i],
                "edfef3ac-9cbe-4fa2-b949-8f29deafd483",
            )
            mock_get_csrs.reset_mock()
