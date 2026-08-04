"""
Portable column types so the same models work against Postgres in
production and SQLite in tests (no live DB needed to run the test suite).
"""
import uuid

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator, CHAR, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB


class GUID(TypeDecorator):
    """Native UUID on Postgres, CHAR(36) string elsewhere."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(str(value)))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


class JSONVariant(TypeDecorator):
    """Native JSONB on Postgres, plain JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())