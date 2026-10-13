import os
import secrets
import json
import urllib.request
import urllib.error
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from flask import Flask, request
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from monitor.backend.db import setting, connect_db
from monitor.backend.routes.auth import auth_bp
from monitor.backend.routes.events import events_bp
from monitor.backend.routes.notes import notes_bp
from common.registration import allowed_origin
from monitor.backend.observability import configure_errors


def create_app(test_config=None):
    configure_errors("mini-monitor")
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.config.from_mapping(
        SECRET_KEY=setting('SECRET_KEY') or secrets.token_hex(32),
        SESSION_COOKIE_NAME='mini_watch_monitor',
        SESSION_COOKIE_SECURE=setting('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
        EVENT_TOKEN=setting('EVENT_TOKEN', ''),
        GENERAL_API_URL=setting('GENERAL_API_URL', 'http://general-api:5000'),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        MAX_CONTENT_LENGTH=1024 * 1024,
        FRONTEND_ORIGIN=setting('FRONTEND_ORIGIN', 'http://127.0.0.1:5173'),
    )
    if test_config:
        app.config.update(test_config)
    for bp in (auth_bp, events_bp, notes_bp):
        app.register_blueprint(bp)

    @app.post('/general-api/auth/register')
    def general_registration():
        # Only the two APIs join the shared network. Keep the existing
        # general signup UI without connecting either gateway to that network.
        if not allowed_origin():
            return {'error': '허용되지 않은 요청 출처입니다.'}, 403
        req = urllib.request.Request(
            app.config['GENERAL_API_URL'].rstrip('/') + '/auth/register',
            data=json.dumps(request.get_json(silent=True)).encode(),
            headers={'Content-Type': 'application/json'},
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                return json.loads(response.read()), response.status
        except urllib.error.HTTPError as error:
            return json.loads(error.read()), error.code
        except (OSError, ValueError):
            return {'error': '일반 서비스에 연결하지 못했습니다.'}, 503

    @app.get('/health')
    def health():
        # Liveness only; authenticated DB requests check actual database access.
        return {'service': 'monitor', 'status': 'ok'}

    @app.errorhandler(psycopg.Error)
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        app.logger.error('Monitor database request failed: %s', type(error).__name__)
        return {'error': 'DB에 연결하지 못했습니다. DB 설정과 준비 상태를 확인해 주세요.'}, 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        return {'error': '요청을 처리할 수 없습니다.', 'status': error.code}, error.code

    @app.after_request
    def no_cache(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5200')))
