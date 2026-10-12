"""Real PostgreSQL tests in a disposable schema, without changing user data.
Run from the project root: python -m unittest discover -s monitor/backend/tests -v
"""
import uuid
import unittest
from pathlib import Path
from unittest.mock import patch
from psycopg import sql
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from monitor.backend.app import create_app
from monitor.backend.db import connect_db, orm_engine
from monitor.backend.repositories import events, notes, users


class MonitorIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = 'monitor_test_' + uuid.uuid4().hex
        with connect_db() as conn:
            conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(cls.schema)))
        cls.addClassCleanup(cls.drop_schema)

        def test_connection():
            conn = connect_db()
            conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(cls.schema)))
            return conn

        cls.test_connection = staticmethod(test_connection)
        cls.prepare_sql = Path(__file__).resolve().parents[1].joinpath('sql/prepare_monitor.sql').read_text(encoding='utf-8')
        with test_connection() as conn:
            conn.execute(cls.prepare_sql)
        test_engine = create_engine(orm_engine.url, connect_args={'options': '-csearch_path=' + cls.schema})
        cls.addClassCleanup(test_engine.dispose)
        patcher = patch.object(users, 'session_scope', sessionmaker(test_engine).begin)
        patcher.start()
        cls.addClassCleanup(patcher.stop)
        for module in (events, notes):
            patcher = patch.object(module, 'connect_db', test_connection)
            patcher.start()
            cls.addClassCleanup(patcher.stop)
        cls.app = create_app({'TESTING': True, 'SECRET_KEY': 'integration-test-secret', 'FRONTEND_ORIGIN': 'http://127.0.0.1:5173'})

    @classmethod
    def drop_schema(cls):
        with connect_db() as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(cls.schema)))

    def setUp(self):
        with self.test_connection() as conn:
            conn.execute('TRUNCATE notes, http_events, monitor_users RESTART IDENTITY')
            conn.execute('INSERT INTO monitor_users (username, password_hash) VALUES (%s, %s)', ('operator', generate_password_hash('test-only-password')))
        self.client = self.app.test_client()

    def login(self):
        response = self.client.post('/api/auth/login', json={'username': 'operator', 'password': 'test-only-password'})
        self.assertEqual(response.status_code, 200)
        return response

    def create_note(self):
        response = self.client.post('/api/notes', json={'title': '  없는 게시글 확인  ', 'body': '  /board/999의 404 확인  ', 'status': '확인 전'})
        self.assertEqual(response.status_code, 201)
        return response.json['note']

    def test_registration_orm_hash_duplicate_and_login(self):
        payload = {'username': ' new_student ', 'password': 'new-test-password', 'password_confirm': 'new-test-password'}
        response = self.client.post('/api/auth/register', json=payload, headers={'Origin': 'http://127.0.0.1:5173'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['user']['username'], 'new_student')
        self.assertNotIn('password', response.get_data(as_text=True))
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)
        saved = users.find_by_username('new_student')
        self.assertNotEqual(saved['password_hash'], payload['password'])
        self.assertTrue(saved['password_hash'].startswith('scrypt:'))
        self.assertTrue(check_password_hash(saved['password_hash'], payload['password']))
        self.assertEqual(self.client.post('/api/auth/register', json=payload).status_code, 409)
        self.assertEqual(users.find_by_username('new_student'), saved)
        response = self.client.post('/api/auth/login', json={'username': 'new_student', 'password': payload['password']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me').json['user']['username'], 'new_student')
        self.assertEqual(self.client.get('/api/notes').status_code, 200)

    def test_registration_validation_origin_and_database_failure(self):
        valid = {'username': 'new_student', 'password': 'test-password', 'password_confirm': 'test-password'}
        for payload in (None, [], {}, {**valid, 'username': 'x'}, {**valid, 'username': 'a b'}, {**valid, 'username': 'x' * 31}, {**valid, 'password': 1}, {**valid, 'password': 'short'}, {**valid, 'password': ' ' * 8}, {**valid, 'password': 'x' * 129}, {**valid, 'password_confirm': 'different'}):
            self.assertEqual(self.client.post('/api/auth/register', json=payload).status_code, 400)
        self.assertEqual(self.client.post('/api/auth/register', json=valid, headers={'Origin': 'https://other.example'}).status_code, 403)
        self.assertIsNone(users.find_by_username('new_student'))
        with patch.object(users, 'session_scope', side_effect=OperationalError('hidden', {}, Exception('offline'))):
            response = self.client.post('/api/auth/register', json=valid)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('hidden', response.get_data(as_text=True))

    def test_login_validation_hash_session_and_logout(self):
        for data in ([], {}, {'username': ' ', 'password': 'x'}, {'username': 'operator', 'password': '  '}, {'username': 1, 'password': 'x'}):
            self.assertEqual(self.client.post('/api/auth/login', json=data).status_code, 400)
        for username, password in [('operator', 'wrong'), ('unknown', 'wrong')]:
            self.assertEqual(self.client.post('/api/auth/login', json={'username': username, 'password': password}).status_code, 401)
        response = self.login()
        self.assertNotIn('password', response.get_data(as_text=True))
        self.assertIn('HttpOnly', response.headers['Set-Cookie'])
        self.assertEqual(self.client.get('/api/auth/me').json['user']['username'], 'operator')
        # A fresh app instance accepts the same signed session cookie.
        restarted = create_app({'TESTING': True, 'SECRET_KEY': 'integration-test-secret'}).test_client()
        cookie = self.client.get_cookie('mini_watch_monitor')
        restarted.set_cookie('mini_watch_monitor', cookie.value)
        self.assertEqual(restarted.get('/api/auth/me').status_code, 200)
        self.assertEqual(self.client.post('/api/auth/logout').status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)
        self.assertEqual(self.client.get('/api/notes').status_code, 401)

    def test_unauthenticated_api_protection_and_forged_cookie(self):
        for path, method in [('/api/events', 'get'), ('/api/notes', 'get'), ('/api/notes/1', 'get'), ('/api/notes', 'post'), ('/api/notes/1', 'put'), ('/api/notes/1', 'delete')]:
            with self.subTest(path=path, method=method):
                self.assertEqual(getattr(self.client, method)(path, json={'title': 'a', 'body': 'b'}).status_code, 401)
        self.client.set_cookie('mini_watch_monitor', 'forged')
        self.assertEqual(self.client.get('/api/notes').status_code, 401)
        self.assertEqual(self.client.post('/api/events', json={'method': 'GET', 'path': '/', 'status_code': 200}).status_code, 201)

    def test_notes_crud_status_cancellation_and_persistence(self):
        self.login()
        self.assertEqual(self.client.get('/api/notes').json['notes'], [])
        note = self.create_note()
        note_id = note['id']
        self.assertEqual(note['title'], '없는 게시글 확인')
        self.assertEqual(note['body'], '/board/999의 404 확인')
        detail = self.client.get(f'/api/notes/{note_id}').json['note']
        # Opening a detail or cancelling an edit/deletion issues no mutation.
        self.assertEqual(detail, self.client.get(f'/api/notes/{note_id}').json['note'])
        response = self.client.put(f'/api/notes/{note_id}', json={'title': '수정된 제목', 'body': '확인하고 완료', 'status': '완료'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['note']['id'], note_id)
        self.assertEqual(notes.find_note(note_id)['status'], '완료')
        self.assertEqual(self.client.get('/api/notes').json['notes'][0]['title'], '수정된 제목')
        self.assertEqual(self.client.post('/api/auth/logout').status_code, 200)
        self.login()
        self.assertEqual(self.client.get(f'/api/notes/{note_id}').json['note']['status'], '완료')
        self.assertEqual(self.client.delete(f'/api/notes/{note_id}').status_code, 200)
        self.assertEqual(self.client.get('/api/notes').json['notes'], [])
        for method in ('get', 'put', 'delete'):
            self.assertEqual(getattr(self.client, method)(f'/api/notes/{note_id}', json={'title': 'a', 'body': 'b'}).status_code, 404)

    def test_invalid_notes_preserve_database_and_form_values(self):
        self.login()
        original = self.create_note()
        for data in ([], {}, {'title': '', 'body': '내용'}, {'title': ' \t\n ', 'body': '내용'}, {'title': '제목', 'body': ''}, {'title': '제목', 'body': ' \n '}, {'title': 'a', 'body': 'b', 'status': 'unknown'}, {'title': 'a', 'body': 'b', 'status': []}):
            with self.subTest(data=data):
                self.assertEqual(self.client.post('/api/notes', json=data).status_code, 400)
                self.assertEqual(self.client.put(f"/api/notes/{original['id']}", json=data).status_code, 400)
                self.assertEqual(len(notes.list_notes()), 1)
                self.assertEqual(notes.find_note(original['id'])['body'], original['body'])
        for method in ('get', 'put', 'delete'):
            self.assertEqual(getattr(self.client, method)('/api/notes/999999', json={}).status_code, 404)

    def test_event_ingestion_filtering_summary_and_persistence(self):
        self.login()
        for method, path, code in [('GET', '/', 200), ('GET', '/board/404', 404), ('POST', '/board/new', 400), ('POST', '/auth/login', 401)]:
            self.assertEqual(self.client.post('/api/events', json={'method': method, 'path': path, 'status_code': code}).status_code, 201)
        data = self.client.get('/api/events').json
        self.assertEqual(data['summary'], {'total': 4, 'errors': 3})
        data = self.client.get('/api/events?path=/board&status=errors').json
        self.assertEqual(data['summary'], {'total': 2, 'errors': 2})
        self.assertEqual(len(self.client.get('/api/events?status=404').json['events']), 1)
        self.assertEqual(len(self.client.get('/api/events?event_type=login_failure').json['events']), 1)
        self.assertEqual(len(self.client.get('/api/events?path=%25').json['events']), 0)
        self.assertEqual(len(events.list_events()), 4)
        self.assertEqual(len(self.client.get('/api/events?path=&status=').json['events']), 4)
        for query in ('status=nope', 'status=99', 'event_type=invalid'):
            self.assertEqual(self.client.get('/api/events?' + query).status_code, 400)
        for data in ([], {}, {'method': 'GET', 'path': '/', 'status_code': True}, {'method': 'GET', 'path': '/', 'status_code': 600}, {'method': 'BOGUS', 'path': '/', 'status_code': 200}):
            self.assertEqual(self.client.post('/api/events', json=data).status_code, 400)

    def test_sql_payload_is_data_repeatable_setup_and_cross_origin(self):
        self.login()
        title = "'; DROP TABLE notes; -- <script>alert(1)</script>"
        response = self.client.post('/api/notes', json={'title': title, 'body': "O'Reilly"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['note']['title'], title)
        with self.test_connection() as conn:
            conn.execute(self.prepare_sql)
            conn.execute(self.prepare_sql)
        self.assertEqual(len(notes.list_notes()), 1)
        response = self.client.delete(f"/api/notes/{response.json['note']['id']}", headers={'Origin': 'https://other.example'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(notes.list_notes()), 1)


if __name__ == '__main__':
    unittest.main()
