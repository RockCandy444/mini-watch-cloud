"""Ensure the existing general signup has one explicit cross-Compose path."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch
from monitor.backend.app import create_app


class SignupProxyTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({'TESTING': True, 'SECRET_KEY': 'test',
                                 'FRONTEND_ORIGIN': 'http://localhost:8082'}).test_client()

    def test_forbidden_origin_never_forwarded(self):
        with patch('urllib.request.urlopen') as send:
            response = self.client.post('/general-api/auth/register', json={},
                                        headers={'Origin': 'https://other.example'})
            self.assertEqual(response.status_code, 403)
            send.assert_not_called()

    def test_fixed_destination_preserves_payload_and_success(self):
        payload = {'username': 'student2', 'password': 'test-only-password',
                   'password_confirm': 'test-only-password'}
        response_body = io.BytesIO(b'{"user":{"username":"student2"}}')
        response_body.status = 201
        with patch('urllib.request.urlopen', return_value=response_body) as send:
            response = self.client.post('/general-api/auth/register', json=payload)
            self.assertEqual(response.status_code, 201)
            forwarded = send.call_args.args[0]
            self.assertEqual(forwarded.full_url, 'http://general-api:5000/auth/register')
            self.assertEqual(json.loads(forwarded.data), payload)

    def test_general_errors_and_unavailability(self):
        error = urllib.error.HTTPError('http://general-api:5000/auth/register', 409, '', {},
                                       io.BytesIO(b'{"error":"duplicate"}'))
        with patch('urllib.request.urlopen', side_effect=error):
            self.assertEqual(self.client.post('/general-api/auth/register', json={}).status_code, 409)
        with patch('urllib.request.urlopen', side_effect=OSError('offline')):
            response = self.client.post('/general-api/auth/register', json={})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('offline', response.get_data(as_text=True))

    def test_other_general_paths_are_not_proxy_endpoints(self):
        self.assertEqual(self.client.get('/general-api/auth/register').status_code, 405)
        self.assertEqual(self.client.post('/general-api/board/new', json={}).status_code, 404)
