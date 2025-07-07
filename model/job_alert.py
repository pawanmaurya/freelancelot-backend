from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import datetime
from model.job import Base  # Use the same Base as Job

class JobAlert(Base):
    __tablename__ = "job_alerts"
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    job_id = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow) 