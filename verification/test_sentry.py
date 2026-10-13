"""Check the guarded exercise endpoint and privacy options without contacting Sentry."""
import os
import sys
import unittest
from unittest.mock import patch

from app import create_app
import observability


class SentryContractTests(unittest.TestCase):
    def test_guard_and_result(self):
        app = create_app({'TESTING': False})
        client = app.test_client()
        with patch('request_logging.requests.post'), patch.dict(os.environ, {'ENABLE_SENTRY_TEST': 'false'}):
            self.assertEqual(client.get('/api/sentry-test').status_code, 404)
        with patch('request_logging.requests.post'), patch.dict(os.environ, {'ENABLE_SENTRY_TEST': 'true'}):
            self.assertEqual(client.get('/api/sentry-test').status_code, 401)
            with client.session_transaction() as session:
                session['user_id'] = 1
            with patch('auth_helpers.user_repository.find_user_by_id', return_value={'id': 1, 'username': 'test'}):
                response = client.get('/api/sentry-test')
            if '--exercise' in sys.argv:
                self.assertEqual(response.status_code, 500)
                print('EXERCISE: authenticated request reproduces division by zero -> 500')
            else:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json, {'result': 1.0})
                print('FIXED: authenticated request -> 200, result 1.0; disabled 404, anonymous 401')

    def test_sentry_privacy_and_environment(self):
        event = {'request': {'data': 'private', 'cookies': 'private', 'headers': 'private',
                             'query_string': 'private', 'method': 'GET'}, 'user': {'id': 'private'}}
        cleaned = observability.remove_request_secrets(event, {})
        self.assertEqual(cleaned, {'request': {'method': 'GET'}})
        with patch.dict(os.environ, {'SENTRY_DSN': '', 'SENTRY_ENVIRONMENT': 'mini-general', 'APP_VERSION': 'test-release'}), patch.object(observability.sentry_sdk, 'init') as init:
            observability.configure_errors('mini-general')
            init.assert_not_called()
        with patch.dict(os.environ, {'SENTRY_DSN': 'https://public@example.invalid/1', 'SENTRY_ENVIRONMENT': 'mini-general', 'APP_VERSION': 'test-release'}), patch.object(observability.sentry_sdk, 'init') as init, patch.object(observability.sentry_sdk, 'set_tag'):
            observability.configure_errors('mini-general')
            options = init.call_args.kwargs
            self.assertEqual(options['environment'], 'mini-general')
            self.assertEqual(options['release'], 'test-release')
            self.assertFalse(options['send_default_pii'])
            self.assertFalse(options['include_local_variables'])
            self.assertEqual(options['max_request_body_size'], 'never')
            self.assertIs(options['before_send'], observability.remove_request_secrets)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]], verbosity=2)
