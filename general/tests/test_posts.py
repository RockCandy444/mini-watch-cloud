"""실제 PostgreSQL의 임시 스키마 및 실제 HTTP 감시 서버로 통합 검증한다.

general 폴더에서: python -m unittest discover -s tests -v
기존 posts/users 테이블은 건드리지 않는다.
"""
import sys
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
import uuid

from psycopg import sql
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.serving import make_server

from app import create_app
from db import connect_db, orm_engine
from repositories import posts, users


class PostsIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = "crud_test_" + uuid.uuid4().hex
        cls.connect = staticmethod(connect_db)
        cls.schema_created = False
        cls.addClassCleanup(cls.cleanup_schema)
        with connect_db() as conn:
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        cls.schema_created = True

        def test_connection():
            conn = connect_db()
            conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(cls.schema)))
            return conn

        cls.test_connection = staticmethod(test_connection)
        with test_connection() as conn:
            # 수업 DB와 같이 자동 번호 설정이 없는 테이블에서 시작한다.
            conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL)")
            conn.execute("INSERT INTO posts VALUES (1, '기존 글 1', '보존할 내용'), (2, '기존 글 2', '보존할 내용')")
            conn.execute("CREATE TABLE users (id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)")
        cls.prepare_sql = Path(__file__).resolve().parents[1].joinpath("sql", "prepare_posts.sql").read_text(encoding="utf-8")
        with test_connection() as conn:
            conn.execute(cls.prepare_sql)
            rows = conn.execute("SELECT id, title FROM posts ORDER BY id").fetchall()
            if [row["id"] for row in rows] != [1, 2]:
                raise AssertionError("DB 준비 과정에서 기존 글이 변경되었습니다.")
            new = conn.execute("INSERT INTO posts (title, body) VALUES ('새 글', '내용') RETURNING id").fetchone()
            if new["id"] != 3:
                raise AssertionError("기존 최대 번호 다음부터 자동 번호를 생성해야 합니다.")
        cls.posts_patch = patch.object(posts, "connect_db", test_connection)
        test_engine = create_engine(orm_engine.url, connect_args={'options': '-csearch_path=' + cls.schema})
        cls.addClassCleanup(test_engine.dispose)
        cls.users_patch = patch.object(users, "session_scope", sessionmaker(test_engine).begin)
        cls.posts_patch.start()
        cls.addClassCleanup(cls.posts_patch.stop)
        cls.users_patch.start()
        cls.addClassCleanup(cls.users_patch.stop)

        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from monitor.backend import app as monitor
        from monitor.backend.repositories import events as monitor_events, users as monitor_users
        with test_connection() as conn:
            conn.execute(Path(__file__).resolve().parents[2].joinpath('monitor/backend/sql/prepare_monitor.sql').read_text(encoding='utf-8'))
        patcher = patch.object(monitor_users, 'session_scope', sessionmaker(test_engine).begin)
        patcher.start()
        cls.addClassCleanup(patcher.stop)
        for module in (monitor_events,):
            patcher = patch.object(module, 'connect_db', test_connection)
            patcher.start()
            cls.addClassCleanup(patcher.stop)
        cls.monitor = monitor
        cls.server = make_server("127.0.0.1", 0, monitor.app)
        cls.addClassCleanup(cls.server.server_close)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.stop_server)
        cls.app = create_app({"TESTING": True, "FRONTEND_ORIGIN": "http://127.0.0.1:5173", "MONITOR_URL": f"http://127.0.0.1:{cls.server.server_port}/api/events"})

    @classmethod
    def cleanup_schema(cls):
        if cls.schema_created:
            with cls.connect() as conn:
                conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))

    @classmethod
    def stop_server(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=3)

    def setUp(self):
        with self.test_connection() as conn:
            conn.execute("TRUNCATE TABLE posts, users RESTART IDENTITY")
        with self.test_connection() as conn:
            conn.execute('TRUNCATE http_events, users RESTART IDENTITY')
            conn.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', ('monitor-test', generate_password_hash('test-only-password')))
        self.client = self.app.test_client()

    def create(self, title="테스트 제목", body="첫째 줄\n둘째 줄"):
        response = self.client.post("/board/new", data={"title": title, "body": body})
        self.assertEqual(response.status_code, 303)
        return int(response.headers["Location"].rsplit("/", 1)[1])

    def test_empty_and_ordered_list_links(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("등록된 게시글이 없습니다.", response.get_data(as_text=True))
        first = self.create("첫 번째")
        second = self.create("두 번째")
        html = self.client.get("/").get_data(as_text=True)
        self.assertLess(html.index("첫 번째"), html.index("두 번째"))
        self.assertIn(f'href="/board/{first}"', html)
        self.assertIn(f'href="/board/{second}"', html)
        self.assertIn('href="/board/new"', html)

    def test_create_trim_refresh_escape_and_persistence(self):
        post_id = self.create("  <script>alert(1)</script>  ", "  첫 줄\n둘째 줄  ")
        self.assertEqual(posts.find_post(post_id)["body"], "첫 줄\n둘째 줄")
        for _ in range(2):
            response = self.client.get(f"/board/{post_id}")
            self.assertEqual(response.status_code, 200)
            self.assertIn("&lt;script&gt;", response.get_data(as_text=True))
            self.assertNotIn("<script>alert(1)</script>", response.get_data(as_text=True))
        self.assertEqual(len(posts.list_posts()), 1)
        restarted = create_app({"TESTING": True, "MONITOR_URL": self.app.config["MONITOR_URL"]}).test_client()
        self.assertEqual(restarted.get(f"/board/{post_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/posts/{post_id}").json["title"], "<script>alert(1)</script>")

    def test_invalid_create_preserves_values_and_database(self):
        for data in ({"title": "", "body": "내용 유지"}, {"title": " \n\t ", "body": "내용 유지"}, {"title": "제목 유지", "body": ""}, {"title": "제목 유지", "body": " \n\t "}, {}):
            with self.subTest(data=data):
                response = self.client.post("/board/new", data=data)
                self.assertEqual(response.status_code, 400)
                html = response.get_data(as_text=True)
                self.assertIn("입력 내용을 확인해 주세요.", html)
                if data.get("title", "").strip():
                    self.assertIn(data["title"], html)
                if data.get("body", "").strip():
                    self.assertIn(data["body"], html)
                self.assertEqual(posts.list_posts(), [])

    def test_edit_prefill_invalid_and_only_target_update(self):
        target = self.create("원래 제목", "원래 내용")
        other = self.create("다른 글", "변경하지 않을 내용")
        html = self.client.get(f"/board/{target}/edit").get_data(as_text=True)
        self.assertIn('value="원래 제목"', html)
        self.assertIn("원래 내용</textarea>", html)
        for data in ({"title": "   ", "body": "바뀐 내용"}, {"title": "바뀐 제목", "body": "   "}, {}):
            response = self.client.post(f"/board/{target}/edit", data=data)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(posts.find_post(target)["title"], "원래 제목")
            self.assertEqual(posts.find_post(target)["body"], "원래 내용")
        response = self.client.post(f"/board/{target}/edit", data={"title": "  바뀐 제목  ", "body": "  바뀐 내용  "})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["Location"], f"/board/{target}")
        self.assertEqual(posts.find_post(target)["title"], "바뀐 제목")
        self.assertIn("바뀐 제목", self.client.get("/").get_data(as_text=True))
        self.assertIn("바뀐 내용", self.client.get(f"/board/{target}").get_data(as_text=True))
        self.assertEqual(posts.find_post(other)["body"], "변경하지 않을 내용")

    def test_delete_get_cancel_post_and_all_missing_routes(self):
        target = self.create()
        other = self.create("남길 글")
        response = self.client.get(f"/board/{target}/delete")
        self.assertEqual(response.status_code, 200)
        self.assertIn("테스트 제목", response.get_data(as_text=True))
        self.assertIn(f'href="/board/{target}">취소', response.get_data(as_text=True))
        self.assertIsNotNone(posts.find_post(target))
        self.assertEqual(self.client.get(f"/board/{target}").status_code, 200)
        response = self.client.post(f"/board/{target}/delete")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["Location"], "/")
        self.assertIsNone(posts.find_post(target))
        self.assertIsNotNone(posts.find_post(other))
        self.assertNotIn("테스트 제목", self.client.get("/").get_data(as_text=True))
        for suffix, method in (("", "get"), ("/edit", "get"), ("/edit", "post"), ("/delete", "get"), ("/delete", "post")):
            with self.subTest(suffix=suffix, method=method):
                response = getattr(self.client, method)(f"/board/{target}{suffix}")
                self.assertEqual(response.status_code, 404)
                self.assertIn("게시글을 찾을 수 없습니다.", response.get_data(as_text=True))

    def test_missing_posts_and_generic_404(self):
        for suffix, method in (("", "get"), ("/edit", "get"), ("/edit", "post"), ("/delete", "get"), ("/delete", "post")):
            response = getattr(self.client, method)(f"/board/999999{suffix}")
            self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get("/unknown-page").status_code, 404)
        self.assertEqual(self.client.get("/posts/999999").status_code, 404)

    def test_sql_input_is_data_and_prepare_is_repeatable(self):
        title = "'; DROP TABLE posts; --"
        post_id = self.create(title, "O'Reilly")
        self.assertEqual(posts.find_post(post_id)["title"], title)
        with self.test_connection() as conn:
            conn.execute(self.prepare_sql)
            conn.execute(self.prepare_sql)
        next_id = self.create("다음 글")
        self.assertGreater(next_id, post_id)
        self.assertEqual(len(posts.list_posts()), 2)

    def test_existing_login_api_and_page(self):
        with self.test_connection() as conn:
            conn.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", ("crud-user", generate_password_hash("test-only-password")))
        self.assertEqual(self.client.get("/login").status_code, 200)
        self.assertEqual(self.client.post("/auth/login", json=[]).status_code, 400)
        self.assertEqual(self.client.post("/auth/login", json={"username": "crud-user", "password": "wrong"}).status_code, 401)
        response = self.client.post("/auth/login", json={"username": " crud-user ", "password": "test-only-password"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["user"]["username"], "crud-user")
        self.assertNotIn("password_hash", response.get_data(as_text=True))

    def test_general_registration_hash_duplicate_and_login(self):
        payload = {'username': ' new_student ', 'password': 'test-password', 'password_confirm': 'test-password'}
        response = self.client.post('/auth/register', json=payload, headers={'Origin': 'http://127.0.0.1:5173'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['user']['username'], 'new_student')
        self.assertNotIn('password', response.get_data(as_text=True))
        saved = users.find_user('new_student')
        self.assertTrue(saved['password_hash'].startswith('scrypt:'))
        self.assertTrue(check_password_hash(saved['password_hash'], payload['password']))
        self.assertEqual(self.client.post('/auth/register', json=payload).status_code, 409)
        self.assertEqual(users.find_user('new_student'), saved)
        self.assertEqual(self.client.post('/auth/login', json={'username': 'new_student', 'password': payload['password']}).status_code, 200)

    def test_general_registration_invalid_payload_and_origin(self):
        valid = {'username': 'new_student', 'password': 'test-password', 'password_confirm': 'test-password'}
        for payload in (None, [], {}, {**valid, 'username': 'x'}, {**valid, 'password': 'short'}, {**valid, 'password_confirm': 'different'}):
            self.assertEqual(self.client.post('/auth/register', json=payload).status_code, 400)
        self.assertEqual(self.client.post('/auth/register', json=valid, headers={'Origin': 'https://other.example'}).status_code, 403)
        self.assertIsNone(users.find_user('new_student'))

    def test_actual_monitor_receives_request_json(self):
        self.client.get("/")
        self.client.post("/board/new", data={"title": "", "body": "내용"})
        self.client.get("/board/999999")
        monitor_client = self.monitor.app.test_client()
        monitor_client.post('/api/auth/login', json={'username': 'monitor-test', 'password': 'test-only-password'})
        events = monitor_client.get("/api/events").json["events"]
        self.assertTrue(any(e["path"] == "/" and e["method"] == "GET" and e["status_code"] == 200 for e in events))
        self.assertTrue(any(e["path"] == "/board/new" and e["method"] == "POST" and e["status_code"] == 400 for e in events))
        self.assertTrue(any(e["path"] == "/board/999999" and e["status_code"] == 404 for e in events))

    def test_monitor_failure_does_not_break_board(self):
        import requests
        with patch("request_logging.requests.post", side_effect=requests.ConnectionError("test-only failure")):
            self.assertEqual(self.client.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
