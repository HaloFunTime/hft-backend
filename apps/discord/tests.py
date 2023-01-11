from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.discord.utils import update_or_create_discord_account


class DiscordAccountTestCase(TestCase):
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

    def test_update_or_create_discord_account(self):
        # New ID & tag should result in account creation
        update_or_create_discord_account("123", "ABC#1234", self.user)
        discord_account_1 = DiscordAccount.objects.get(discord_id="123")
        self.assertIsNotNone(discord_account_1)
        self.assertEqual(discord_account_1.discord_id, "123")
        self.assertEqual(discord_account_1.discord_tag, "ABC#1234")
        self.assertIsNotNone(discord_account_1.created_at)
        self.assertIsNotNone(discord_account_1.updated_at)
        self.assertEqual(len(DiscordAccount.objects.all()), 1)

        # Same ID with new tag should result in account update
        update_or_create_discord_account("123", "DEF#1234", self.user)
        discord_account_2 = DiscordAccount.objects.get(discord_id="123")
        self.assertIsNotNone(discord_account_2)
        self.assertEqual(discord_account_2.discord_id, "123")
        self.assertEqual(discord_account_2.discord_tag, "DEF#1234")
        self.assertIsNotNone(discord_account_2.created_at)
        self.assertIsNotNone(discord_account_2.updated_at)
        self.assertNotEqual(discord_account_1.updated_at, discord_account_2.updated_at)
        self.assertEqual(len(DiscordAccount.objects.all()), 1)

        # New ID but same tag should result in second account creation
        update_or_create_discord_account("456", "DEF#1234", self.user)
        discord_account_3 = DiscordAccount.objects.get(discord_id="456")
        self.assertIsNotNone(discord_account_3)
        self.assertEqual(discord_account_3.discord_id, "456")
        self.assertEqual(discord_account_3.discord_tag, "DEF#1234")
        self.assertIsNotNone(discord_account_3.created_at)
        self.assertIsNotNone(discord_account_3.updated_at)
        self.assertEqual(len(DiscordAccount.objects.all()), 2)
