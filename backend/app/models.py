from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=True)
    sender = Column(String, nullable=True)
    received_time = Column(DateTime, nullable=True)
    body = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)