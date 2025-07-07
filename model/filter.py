from sqlalchemy import Column, String, Float, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class Filter(Base):
    __tablename__ = "filters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String)
    min_price = Column(Numeric)
    max_price = Column(Numeric)
    created_at = Column(DateTime)
    keywords = relationship("FilterKeyword", back_populates="filter")
    categories = relationship("FilterCategory", back_populates="filter")

class FilterKeyword(Base):
    __tablename__ = "filter_keywords"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filter_id = Column(UUID(as_uuid=True), ForeignKey("filters.id"), nullable=False)
    keyword = Column(String)
    filter = relationship("Filter", back_populates="keywords")

class FilterCategory(Base):
    __tablename__ = "filter_categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filter_id = Column(UUID(as_uuid=True), ForeignKey("filters.id"), nullable=False)
    category = Column(String)
    filter = relationship("Filter", back_populates="categories")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan = Column(String)
    telegram_id = Column(String)
    created_at = Column(DateTime) 