import pytest
from db.session import SessionLocal

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
