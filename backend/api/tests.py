# backend/api/tests.py
from http import HTTPStatus

from django.test import Client, TestCase


class FoodgramAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_list_exists(self):
        """Проверка доступности API."""
        response = self.guest_client.get('/api/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
