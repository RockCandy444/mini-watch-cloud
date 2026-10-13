import unittest
from unittest.mock import patch
import psycopg
from monitor.backend.app import create_app


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({'TESTING': True, 'SECRET_KEY': 'test'}).test_client()

    def test_health_is_liveness_and_does_not_query_database(self):
        with patch('monitor.backend.app.connect_db') as connection:
            response = self.client.get('/health')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {'service': 'monitor', 'status': 'ok'})
            connection.assert_not_called()

    def test_health_does_not_claim_database_readiness(self):
        with patch('monitor.backend.app.connect_db', side_effect=psycopg.OperationalError('private details')):
            response = self.client.get('/health')
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('private details', response.get_data(as_text=True))
            self.assertNotIn('database', response.json)
