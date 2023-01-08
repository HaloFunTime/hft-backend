import datetime
import uuid

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.intern.models import (
    InternChatter,
    InternChatterForbiddenChannel,
    InternChatterPause,
    InternHelpfulHint,
)
from apps.intern.views import (
    INTERN_CHATTER_DEFAULT_MESSAGE,
    INTERN_CHATTER_ERROR_CHANNEL_FORBIDDEN,
    INTERN_CHATTER_ERROR_INVALID_CHANNEL_ID,
    INTERN_CHATTER_ERROR_MISSING_CHANNEL_ID,
    INTERN_CHATTER_ERROR_PAUSED,
    INTERN_CHATTER_PAUSE_ERROR_MISSING_ID,
    INTERN_CHATTER_PAUSE_ERROR_MISSING_TAG,
    INTERN_HELPFUL_HINT_DEFAULT_MESSAGE,
)


def chatter_factory(creator: User, message_text: str = None) -> InternChatter:
    return InternChatter.objects.create(
        creator=creator,
        message_text=uuid.uuid4().hex if message_text is None else message_text,
    )


def chatter_forbidden_channel_factory(
    creator: User, discord_channel_id: int = None
) -> InternChatterForbiddenChannel:
    return InternChatterForbiddenChannel.objects.create(
        creator=creator,
        discord_channel_id=abs(uuid.uuid4().int) % 2147483647
        if discord_channel_id is None
        else discord_channel_id,
    )


def chatter_pause_factory(
    creator: User, discord_user_id: int = None
) -> InternChatterPause:
    return InternChatterPause.objects.create(
        creator=creator,
        discord_user_id=abs(uuid.uuid4().int) % 2147483647
        if discord_user_id is None
        else discord_user_id,
    )


def helpful_hint_factory(creator: User, message_text: str = None) -> InternHelpfulHint:
    return InternHelpfulHint.objects.create(
        creator=creator,
        message_text=uuid.uuid4().hex if message_text is None else message_text,
    )


class InternChatterTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_intern_random_chatter(self):
        # Missing channelId query parameter throws error
        response = self.client.get("/intern/random-chatter")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {"error": INTERN_CHATTER_ERROR_MISSING_CHANNEL_ID}
        )

        # Invalid channelId query parameter throws error
        response = self.client.get("/intern/random-chatter?channelId=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {"error": INTERN_CHATTER_ERROR_INVALID_CHANNEL_ID}
        )

        # Empty InternChatter table returns default chatter message
        response = self.client.get(
            "/intern/random-chatter?channelId=471730128335142912"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"chatter": INTERN_CHATTER_DEFAULT_MESSAGE})

        # Forbidden channel throws error
        forbidden_channel_id = 471730128335142911
        chatter_forbidden_channel_factory(self.user, forbidden_channel_id)
        response = self.client.get(
            f"/intern/random-chatter?channelId={forbidden_channel_id}"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data, {"error": INTERN_CHATTER_ERROR_CHANNEL_FORBIDDEN}
        )

        # Pause record created within the past hour throws error
        chatter_pause = chatter_pause_factory(self.user)
        response = self.client.get(
            "/intern/random-chatter?channelId=471730128335142912"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {"error": INTERN_CHATTER_ERROR_PAUSED})

        # Pause record created an hour ago does not throw error (default chatter returned)
        chatter_pause.created_at = datetime.datetime.now() - datetime.timedelta(hours=1)
        chatter_pause.save()
        response = self.client.get(
            "/intern/random-chatter?channelId=471730128335142912"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"chatter": INTERN_CHATTER_DEFAULT_MESSAGE})

        # Returned chatter matches record (if there's only one in the table)
        chatter_message_text = "This is my test chatter message."
        chatter_factory(self.user, chatter_message_text)
        response = self.client.get(
            "/intern/random-chatter?channelId=471730128335142912"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"chatter": chatter_message_text})

    def test_intern_chatter_pause(self):
        # Missing 'discordUserId' throws error
        response = self.client.post("/intern/pause-chatter", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {"error": INTERN_CHATTER_PAUSE_ERROR_MISSING_ID}
        )

        # Non-numeric 'discordUserId' throws error
        response = self.client.post(
            "/intern/pause-chatter", {"discordUserId": "abc"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {"error": INTERN_CHATTER_PAUSE_ERROR_MISSING_ID}
        )

        # Missing 'discordUserTag' throws error
        response = self.client.post(
            "/intern/pause-chatter", {"discordUserId": "1234"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {"error": INTERN_CHATTER_PAUSE_ERROR_MISSING_TAG}
        )

        # Invalid 'discordUserTag' throws error
        response = self.client.post(
            "/intern/pause-chatter",
            {"discordUserId": "1234", "discordUserTag": "foo"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {"error": INTERN_CHATTER_PAUSE_ERROR_MISSING_TAG}
        )

        # Valid 'discordUserId' and 'discordUserTag' results in record creation
        response = self.client.post(
            "/intern/pause-chatter",
            {"discordUserId": "1234", "discordUserTag": "HFTIntern#1234"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"success": True})
        self.assertEqual(InternChatterPause.objects.count(), 1)


class InternHelpfulHintTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_intern_random_helpful_hint(self):
        # Empty InternHelpfulHint table returns default hint message
        response = self.client.get("/intern/random-helpful-hint")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"hint": INTERN_HELPFUL_HINT_DEFAULT_MESSAGE})

        # Returned hint matches record (if there's only one in the table)
        hint_message_text = "This is my test hint message."
        helpful_hint_factory(self.user, hint_message_text)
        response = self.client.get("/intern/random-helpful-hint")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"hint": hint_message_text})
