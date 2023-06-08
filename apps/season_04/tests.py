import datetime

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.season_04.models import StampChampEarner


class Season04TestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_stamp_champ_earner_save(self):
        # Creating a StampChampEarner record should be successful
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="test", discord_username="ABC1234"
        )
        stamp_champ_earner = StampChampEarner.objects.create(
            creator=self.user,
            earner=discord_account,
            earned_at=datetime.datetime(2023, 6, 7, 0, 0, 0),
        )
        self.assertEqual(stamp_champ_earner.creator, self.user)
        self.assertEqual(stamp_champ_earner.earner_id, discord_account.discord_id)
        self.assertEqual(
            stamp_champ_earner.earned_at, datetime.datetime(2023, 6, 7, 0, 0, 0)
        )
        self.assertEqual(discord_account.stamp_champ_earner, stamp_champ_earner)

        # Duplicate StampChampEarner record (same `earner`) should fail to save
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "StampChampEarner_earner_id_key"\n'
            + "DETAIL:  Key (earner_id)=(test) already exists.\n",
            StampChampEarner.objects.create,
            creator=self.user,
            earner=discord_account,
            earned_at=datetime.datetime(2023, 7, 7, 0, 0, 0),
        )
