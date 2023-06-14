import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.fun_time_friday.models import (
    FunTimeFridayVoiceConnect,
    FunTimeFridayVoiceDisconnect,
)
from apps.fun_time_friday.utils import get_voice_connections


class FunTimeFridayUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_get_voice_connections(self):
        # Create test data
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="test", discord_username="ABC1234"
        )

        # No voice connections means empty list result
        result = get_voice_connections(
            discord_account,
            datetime.datetime.now(tz=datetime.timezone.utc),
            datetime.datetime.now(tz=datetime.timezone.utc),
        )
        self.assertEqual(result, [])

        # One matching connect & disconnect
        ftf_c_1 = FunTimeFridayVoiceConnect.objects.create(
            creator=self.user,
            connector_discord=discord_account,
            connected_at=datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=11,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="1",
        )
        ftf_d_1 = FunTimeFridayVoiceDisconnect.objects.create(
            creator=self.user,
            disconnector_discord=discord_account,
            disconnected_at=datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=1,
                minute=12,
                second=49,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="1",
        )
        result = get_voice_connections(
            discord_account,
            datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            datetime.datetime(
                year=2023,
                month=8,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(
            result,
            [
                {
                    "channel_id": "1",
                    "connect": ftf_c_1,
                    "disconnect": ftf_d_1,
                    "time_connected": datetime.timedelta(
                        hours=1, minutes=12, seconds=38
                    ),
                }
            ],
        )

        # Orphan connect before matching pair
        ftf_c_orphan_single_before = FunTimeFridayVoiceConnect.objects.create(
            creator=self.user,
            connector_discord=discord_account,
            connected_at=datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="orphan_c_before",
        )
        result = get_voice_connections(
            discord_account,
            datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            datetime.datetime(
                year=2023,
                month=8,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(
            result,
            [
                {
                    "channel_id": "1",
                    "connect": ftf_c_1,
                    "disconnect": ftf_d_1,
                    "time_connected": datetime.timedelta(
                        hours=1, minutes=12, seconds=38
                    ),
                }
            ],
        )
        ftf_c_orphan_single_before.delete()

        # Orphan disconnect before matching pair
        ftf_d_orphan_single_before = FunTimeFridayVoiceDisconnect.objects.create(
            creator=self.user,
            disconnector_discord=discord_account,
            disconnected_at=datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="orphan_d_before",
        )
        result = get_voice_connections(
            discord_account,
            datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            datetime.datetime(
                year=2023,
                month=8,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(
            result,
            [
                {
                    "channel_id": "1",
                    "connect": ftf_c_1,
                    "disconnect": ftf_d_1,
                    "time_connected": datetime.timedelta(
                        hours=1, minutes=12, seconds=38
                    ),
                }
            ],
        )
        ftf_d_orphan_single_before.delete()

        # Orphan connect and disconnect before matching pair (should discard both)
        FunTimeFridayVoiceConnect.objects.create(
            creator=self.user,
            connector_discord=discord_account,
            connected_at=datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="orphan_c_both_1",
        )
        FunTimeFridayVoiceDisconnect.objects.create(
            creator=self.user,
            disconnector_discord=discord_account,
            disconnected_at=datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="orphan_d_both_1",
        )
        result = get_voice_connections(
            discord_account,
            datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            datetime.datetime(
                year=2023,
                month=8,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(
            result,
            [
                {
                    "channel_id": "1",
                    "connect": ftf_c_1,
                    "disconnect": ftf_d_1,
                    "time_connected": datetime.timedelta(
                        hours=1, minutes=12, seconds=38
                    ),
                }
            ],
        )

        # Second set of orphan connect and disconnects before matching pair (should discard as well)
        FunTimeFridayVoiceConnect.objects.create(
            creator=self.user,
            connector_discord=discord_account,
            connected_at=datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=1,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="orphan_c_both_2",
        )
        FunTimeFridayVoiceDisconnect.objects.create(
            creator=self.user,
            disconnector_discord=discord_account,
            disconnected_at=datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=1,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="orphan_d_both_2",
        )
        result = get_voice_connections(
            discord_account,
            datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            datetime.datetime(
                year=2023,
                month=8,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(
            result,
            [
                {
                    "channel_id": "1",
                    "connect": ftf_c_1,
                    "disconnect": ftf_d_1,
                    "time_connected": datetime.timedelta(
                        hours=1, minutes=12, seconds=38
                    ),
                }
            ],
        )

        # Orphan connect after matching pair
        ftf_c_orphan_single_after = FunTimeFridayVoiceConnect.objects.create(
            creator=self.user,
            connector_discord=discord_account,
            connected_at=datetime.datetime(
                year=2023,
                month=7,
                day=2,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="orphan_c_after",
        )
        result = get_voice_connections(
            discord_account,
            datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            datetime.datetime(
                year=2023,
                month=8,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(
            result,
            [
                {
                    "channel_id": "1",
                    "connect": ftf_c_1,
                    "disconnect": ftf_d_1,
                    "time_connected": datetime.timedelta(
                        hours=1, minutes=12, seconds=38
                    ),
                }
            ],
        )
        ftf_c_orphan_single_after.delete()

        # Orphan disconnect after matching pair
        ftf_d_orphan_single_after = FunTimeFridayVoiceDisconnect.objects.create(
            creator=self.user,
            disconnector_discord=discord_account,
            disconnected_at=datetime.datetime(
                year=2023,
                month=7,
                day=2,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            channel_id="orphan_d_after",
        )
        result = get_voice_connections(
            discord_account,
            datetime.datetime(
                year=2023,
                month=7,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
            datetime.datetime(
                year=2023,
                month=8,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(
            result,
            [
                {
                    "channel_id": "1",
                    "connect": ftf_c_1,
                    "disconnect": ftf_d_1,
                    "time_connected": datetime.timedelta(
                        hours=1, minutes=12, seconds=38
                    ),
                }
            ],
        )
        ftf_d_orphan_single_after.delete()
