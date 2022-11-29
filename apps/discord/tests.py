from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.discord.models import DiscordAccount


class XboxLiveAccountTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_discord_account_save(self):
        # Creating an account should be successful
        account = DiscordAccount.objects.create(
            creator=self.user, discord_id="test", discord_tag="ABC#1234"
        )
        self.assertEqual(account.creator, self.user)
        self.assertEqual(account.discord_id, "test")
        self.assertEqual(account.discord_tag, "ABC#1234")

        # Duplicate account (same `discord_id`) should fail to save
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "DiscordAccount_pkey"\n'
            + "DETAIL:  Key (discord_id)=(test) already exists.\n",
            DiscordAccount.objects.create,
            creator=self.user,
            discord_id="test",
        )
