import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from monitor.backend.db import connect_db

if __name__ == '__main__':
    with connect_db() as conn:
        conn.execute(Path(__file__).with_name('sql').joinpath('prepare_monitor.sql').read_text(encoding='utf-8'))
    print('감시 DB 테이블 준비 완료 (기존 데이터 유지)')
