from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.db import session as session_module
from app.models import User, UserRole


def test_dependency_rolls_back_uncommitted_writes(db_session, monkeypatch):
    factory = sessionmaker(bind=db_session.get_bind())
    monkeypatch.setattr(session_module, "get_session_factory", lambda: factory)
    dependency = session_module.get_db()
    session = next(dependency)
    session.add(User(
        first_name="Ada", last_name="Lovelace", email="ada@example.com",
        role=UserRole.STUDENT,
    ))
    session.flush()
    dependency.close()

    with factory() as verification_session:
        assert verification_session.scalar(select(func.count()).select_from(User)) == 0
