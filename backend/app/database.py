# app/database.py
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite DB file stored in backend folder
DATABASE_URL = "sqlite:///./emails.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class EmailModel(Base):
    __tablename__ = "emails"

    id            = Column(String, primary_key=True)
    subject       = Column(String, index=True)
    sender        = Column(String)
    sender_email  = Column(String)
    body          = Column(Text)
    summary       = Column(Text)
    action_items  = Column(Text)    # stored as JSON string
    priority      = Column(String)
    received_time = Column(String)


# Create table if it doesn't exist
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()