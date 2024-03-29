from unittest.mock import patch

from django.db import OperationalError
from rest_framework.test import APIClient, APITestCase


class PingTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.ping.views.connections.all")
    def test_ping_failure_database_connectivity(self, mock_all):
        mock_all.return_value = []

        response = self.client.get("/ping/")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {"detail": "Database connectivity error", "success": False},
        )

    @patch("apps.ping.views.random")
    def test_ping_failure_health_check(self, mock_random):
        mock_cursor = mock_random.choice.return_value.cursor
        mock_execute = mock_cursor.return_value.execute
        mock_cursor.return_value.fetchone.return_value.__getitem__.return_value = 0

        response = self.client.get("/ping/")

        mock_execute.assert_called_once_with("SELECT 1")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {"detail": "Health check error", "success": False},
        )

    @patch("apps.ping.views.random")
    def test_ping_failure_operational_error(self, mock_random):
        mock_execute = mock_random.choice.return_value.cursor.return_value.execute
        mock_execute.side_effect = OperationalError()

        response = self.client.get("/ping/")

        mock_execute.assert_called_once_with("SELECT 1")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {"detail": "Operational error", "success": False},
        )

    def test_ping_success(self):
        response = self.client.get("/ping/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"detail": "The HaloFunTime API is available", "success": True},
        )
