import datetime

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.season_06.models import BingoBuff


class Season06TestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_bingo_buff_save(self):
        # Creating a BingoBuff record should be successful
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="test", discord_username="ABC1234"
        )
        bingo_buff = BingoBuff.objects.create(
            creator=self.user,
            earner=discord_account,
            earned_at=datetime.datetime(
                2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
        self.assertEqual(bingo_buff.creator, self.user)
        self.assertEqual(bingo_buff.earner_id, discord_account.discord_id)
        self.assertEqual(
            bingo_buff.earned_at,
            datetime.datetime(2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(discord_account.bingo_buff, bingo_buff)

        # Duplicate BingoBuff record (same `earner`) should fail to save
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "BingoBuff_earner_id_key"\n'
            + "DETAIL:  Key (earner_id)=(test) already exists.\n",
            BingoBuff.objects.create,
            creator=self.user,
            earner=discord_account,
            earned_at=datetime.datetime(
                2023, 7, 7, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
