import datetime

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.season_05.models import DomainChallengeTeamAssignment, DomainMaster


class Season05TestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_join_challenge_view(self):
        # Missing field values throw errors
        response = self.client.post("/season-05/join-challenge", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-05/join-challenge",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )

        # New assignment
        response = self.client.post(
            "/season-05/join-challenge",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(DomainChallengeTeamAssignment.objects.all().count(), 1)
        assignment_record = DomainChallengeTeamAssignment.objects.first()
        self.assertEqual(assignment_record.assignee_id, "123")
        self.assertIsNotNone(assignment_record.team)
        self.assertIsNotNone(response.data.get("assignedTeam"))
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), True)
        initial_team = assignment_record.team

        # Existing assignment
        response = self.client.post(
            "/season-05/join-challenge",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(DomainChallengeTeamAssignment.objects.all().count(), 1)
        assignment_record = DomainChallengeTeamAssignment.objects.first()
        self.assertEqual(assignment_record.assignee_id, "123")
        self.assertIsNotNone(assignment_record.team)
        self.assertEqual(response.data.get("assignedTeam"), initial_team)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), False)

    def test_save_master_view(self):
        # Missing field values throw errors
        response = self.client.post("/season-05/save-master", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("domainsMastered", details)
        self.assertEqual(
            details.get("domainsMastered"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-05/save-master",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
                "domainsMastered": "not_an_int",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )
        self.assertIn("domainsMastered", details)
        self.assertEqual(
            details.get("domainsMastered")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )

        # New master
        now_before_post = datetime.datetime.now(tz=datetime.timezone.utc)
        response = self.client.post(
            "/season-05/save-master",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
                "domainsMastered": 10,
            },
            format="json",
        )
        self.assertEqual(DomainMaster.objects.all().count(), 1)
        master_record = DomainMaster.objects.first()
        self.assertEqual(master_record.master_id, "123")
        self.assertGreaterEqual(master_record.mastered_at, now_before_post)
        self.assertEqual(master_record.domain_count, 10)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMaster"), True)
        initial_mastered_at = master_record.mastered_at

        # Existing master, domain count update
        response = self.client.post(
            "/season-05/save-master",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "domainsMastered": 11,
            },
            format="json",
        )
        self.assertEqual(DomainMaster.objects.all().count(), 1)
        master_record = DomainMaster.objects.first()
        self.assertEqual(master_record.master_id, "123")
        self.assertGreaterEqual(master_record.mastered_at, initial_mastered_at)
        self.assertEqual(master_record.domain_count, 11)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMaster"), False)
