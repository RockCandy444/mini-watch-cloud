import os
from pathlib import Path
import psycopg
from dotenv import dotenv_values
from psycopg.rows import dict_row
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

SETTINGS = dotenv_values(Path(__file__).with_name('.env'))


def setting(name, default=None):
    # Keep separate service settings when both apps are tested in one process.
    return os.environ.get('MONITOR_' + name, SETTINGS.get(name, os.environ.get(name, default)))


def connect_db():
    return psycopg.connect(
        host=setting('DB_HOST', '127.0.0.1'), port=setting('DB_PORT', '5432'),
        dbname=setting('DB_NAME', 'monitor_db'), user=setting('DB_USER', 'postgres'),
        password=setting('DB_PASSWORD'), connect_timeout=3, row_factory=dict_row,
    )


orm_engine = create_engine(
    URL.create("postgresql+psycopg", username=setting("DB_USER", "postgres"),
               password=setting("DB_PASSWORD"), host=setting("DB_HOST", "127.0.0.1"),
               port=int(setting("DB_PORT", "5432")), database=setting("DB_NAME", "monitor_db")),
    pool_pre_ping=True, connect_args={"connect_timeout": 3}, hide_parameters=True,
)
session_scope = sessionmaker(orm_engine).begin
