import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.trailblazer.models import TrailblazerTuesdayAttendance
from apps.trailblazer.utils import get_e1_discord_earn_dict, get_e2_discord_earn_dict


class TrailblazerUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_get_e1_discord_earn_dict(self):
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
        earn_dict = get_e1_discord_earn_dict([])
        self.assertEqual(earn_dict, {})

        # Max Points - exactly
        cotcs = []
        for i in range(5):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2024, 1, 30),
                )
            )
        earn_dict = get_e1_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 250
        )

        # Max points - overages
        for i in range(2):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2024, 1, 30),
                )
            )
        earn_dict = get_e1_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 250
        )

        # Deletion of all records eliminates points
        for cotc in cotcs:
            cotc.delete()
        earn_dict = get_e1_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 0
        )

        # Addition of records outside the date range still results in no points
        cotcs = []
        for i in range(5):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 7, 11),
                )
            )
        earn_dict = get_e1_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 0
        )

    def test_get_e2_discord_earn_dict(self):
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
        earn_dict = get_e2_discord_earn_dict([])
        self.assertEqual(earn_dict, {})

        # Max Points - exactly
        cotcs = []
        for i in range(5):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2024, 6, 4),
                )
            )
        earn_dict = get_e2_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 250
        )

        # Max points - overages
        for i in range(2):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2024, 6, 4),
                )
            )
        earn_dict = get_e2_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 250
        )

        # Deletion of all records eliminates points
        for cotc in cotcs:
            cotc.delete()
        earn_dict = get_e2_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 0
        )

        # Addition of records outside the date range still results in no points
        cotcs = []
        for i in range(5):
            cotcs.append(
                TrailblazerTuesdayAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 7, 11),
                )
            )
        earn_dict = get_e2_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["church_of_the_crab"], 0
        )
