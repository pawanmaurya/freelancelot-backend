from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)  # Upwork ID
    title = Column(String)
    url = Column(String)
    category = Column(String)
    type = Column(String)
    description = Column(String)
    skills = Column(String)  # store as comma-separated string for now
    budget = Column(Float)
    location = Column(String)
    client_spend = Column(Float)
    client_rating = Column(Float)
    published_at = Column(DateTime)
