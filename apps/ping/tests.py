from django.test import TestCase


class PingTestCase(TestCase):
    def setUp(self):
        print("Called setUp")

    def test_ping(self):
        """Animals that can speak are correctly identified"""
        print("Called test_ping")
