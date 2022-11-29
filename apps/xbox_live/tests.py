from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.xbox_live.models import XboxLiveAccount
from apps.xbox_live.utils import get_xuid_for_gamertag


class XboxLiveAccountTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_xbox_live_account_save(self):
        # Creating an account should be successful
        account = XboxLiveAccount(creator=self.user, gamertag="test")
        account.save()
        self.assertIsNotNone(account.id)
        self.assertEqual(account.gamertag, "test")

        # TODO: Update this part to verify xuid primary key collision is not allowed
        # Duplicate account should fail to save
        account2 = XboxLiveAccount(creator=self.user, gamertag="test")
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "XboxLiveAccount_gamertag_key"',
            account2.save,
        )


class XboxLiveUtilsTestCase(TestCase):
    def test_get_xuid_for_gamertag(self):
        # Utility method should always return the empty string (for now...)
        self.assertEqual(get_xuid_for_gamertag("HFT Intern"), "")
        self.assertEqual(get_xuid_for_gamertag("foo"), "")
        self.assertEqual(get_xuid_for_gamertag("bar"), "")
        self.assertEqual(get_xuid_for_gamertag("baz"), "")
        self.assertEqual(get_xuid_for_gamertag(""), "")
