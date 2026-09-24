from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    # Resolve configuration lazily so health checks do not need a database.
    url = make_url(str(get_settings().database_url))
    url = url.set(drivername="postgresql+psycopg")
    return create_engine(url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped session; callers explicitly commit writes.

    Closing the session also rolls back any uncommitted transaction.
    """
    with get_session_factory()() as session:
        yield session
