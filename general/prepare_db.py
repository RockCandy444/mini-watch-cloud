from pathlib import Path

from db import connect_db


if __name__ == "__main__":
    sql = Path(__file__).with_name("sql").joinpath("prepare_posts.sql").read_text(encoding="utf-8")
    with connect_db() as conn:
        conn.execute(sql)
        conn.execute(Path(__file__).with_name("sql").joinpath("prepare_users.sql").read_text(encoding="utf-8"))
    print("posts/users 테이블과 게시글 자동 번호 설정을 준비했습니다. 기존 자료는 유지됩니다.")
