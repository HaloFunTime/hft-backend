import datetime

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.season_05.models import DomainMaster


class Season05TestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_domain_master_save(self):
        # Creating a DomainMaster record should be successful
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="test", discord_username="ABC1234"
        )
        domain_master = DomainMaster.objects.create(
            creator=self.user,
            master=discord_account,
            mastered_at=datetime.datetime(
                2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
        self.assertEqual(domain_master.creator, self.user)
        self.assertEqual(domain_master.master_id, discord_account.discord_id)
        self.assertEqual(
            domain_master.mastered_at,
            datetime.datetime(2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(discord_account.domain_master, domain_master)

        # Duplicate DomainMaster record (same `master`) should fail to save
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "DomainMaster_master_id_key"\n'
            + "DETAIL:  Key (master_id)=(test) already exists.\n",
            DomainMaster.objects.create,
            creator=self.user,
            master=discord_account,
            mastered_at=datetime.datetime(
                2023, 7, 7, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
