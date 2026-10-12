import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask import Flask, render_template
import psycopg
from sqlalchemy.exc import SQLAlchemyError

from request_logging import register_request_logging
from routes.auth import auth_bp
from routes.posts import posts_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.config.from_mapping(
        MONITOR_URL=os.environ.get("MONITOR_URL", "http://127.0.0.1:5200/api/events"),
        FRONTEND_ORIGIN=os.environ.get("FRONTEND_ORIGIN", "http://127.0.0.1:5173"),
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(posts_bp)
    app.register_blueprint(auth_bp)
    register_request_logging(app)

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
    app.run(host="127.0.0.1", port=5100)
