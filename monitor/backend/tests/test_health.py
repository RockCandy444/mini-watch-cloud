import unittest
from unittest.mock import patch
import psycopg
from monitor.backend.app import create_app


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({'TESTING': True, 'SECRET_KEY': 'test'}).test_client()

    def test_ready_requires_a_successful_database_query(self):
        with patch('monitor.backend.app.connect_db') as connection:
            response = self.client.get('/health')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['database'], 'ready')
            connection.return_value.__enter__.return_value.execute.assert_called_once_with('SELECT 1')

    def test_failed_database_returns_503_without_details(self):
        with patch('monitor.backend.app.connect_db', side_effect=psycopg.OperationalError('private details')):
            response = self.client.get('/health')
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private details', response.get_data(as_text=True))
