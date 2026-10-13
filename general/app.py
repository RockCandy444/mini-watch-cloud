import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask import Flask, render_template, abort
import psycopg
from sqlalchemy.exc import SQLAlchemyError

from request_logging import register_request_logging
from routes.auth import auth_bp
from routes.posts import posts_bp
from auth_helpers import configure_session, api_access_error, no_cache
from observability import configure_errors


def create_app(test_config=None):
    configure_errors("mini-general")
    app = Flask(__name__)
    configure_session(app, "mini_watch_general")
    app.json.ensure_ascii = False
    app.config.from_mapping(
        MONITOR_URL=os.environ.get("MONITOR_URL", "http://127.0.0.1:5200/api/events"),
        FRONTEND_ORIGIN=os.environ.get("FRONTEND_ORIGIN", "http://127.0.0.1:5173"),
        EVENT_TOKEN=os.environ.get("EVENT_TOKEN", ""),
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(posts_bp)
    app.register_blueprint(auth_bp)
    app.after_request(no_cache)
    register_request_logging(app)

    @app.get("/health")
    def health():
        return {"service": "general", "status": "ok"}

    @app.get("/api/sentry-test")
    def sentry_test():
        if os.environ.get("ENABLE_SENTRY_TEST", "false").lower() != "true":
            abort(404)
        error = api_access_error()
        if error:
            return error
        # The exercise is complete: keep the login/feature guards and return JSON.
        result = 1 / 1
        return {"result": result}

    @app.errorhandler(psycopg.Error)
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        app.logger.error("General database request failed: %s", type(error).__name__)
        return {"error": "DB에 연결하지 못했습니다. DB 설정과 준비 상태를 확인해 주세요."}, 503

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", message="요청한 페이지를 찾을 수 없습니다."), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5100")))
