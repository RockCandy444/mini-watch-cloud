import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(Path(__file__).with_name(".env"))

orm_engine = create_engine(
    URL.create("postgresql+psycopg", username=os.environ.get("DB_USER", "postgres"),
               password=os.environ.get("DB_PASSWORD"), host=os.environ.get("DB_HOST", "127.0.0.1"),
               port=int(os.environ.get("DB_PORT", "5432")), database=os.environ.get("DB_NAME", "general_db")),
    pool_pre_ping=True, connect_args={"connect_timeout": 3}, hide_parameters=True,
)
session_scope = sessionmaker(orm_engine).begin


def connect_db():
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=3,
        row_factory=dict_row,
    )
