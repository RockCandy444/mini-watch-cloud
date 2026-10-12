from sqlalchemy import Identity, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MonitorUser(Base):
    __tablename__ = "monitor_users"

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
