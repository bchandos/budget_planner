# pylint: disable=no-member

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

# an Engine, which the Session will use for connection resources
# For demo purposes, use in memory sqlite DB
engine = create_engine('sqlite://')
# Real connection here, e.g...
# engine = create_engine('mysql://db_user:tiger@hostname/dbname', encoding='latin1', echo=True)

# create a configured "Session" class
Session = sessionmaker(bind=engine)

# create tables if they do not exist
Base.metadata.create_all(bind=engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations.
    Usage:
        with session_scope() as session:
            session.query(...)
    """

    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
