import uuid
from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from .db.database import Base, engine

# Helper for portable Array support (PostgreSQL ARRAY vs simple JSON list fallback for SQLite)
class ARRAY_MOCK(JSON):
    pass

class AutoMLRun(Base):
    __tablename__ = "runs"

    # Use string type for UUID compatibility on SQLite, convert in Postgres
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    dataset_name = Column(String(255), nullable=False)
    target_variable = Column(String(255), nullable=False)
    task_type = Column(String(50), nullable=False)
    selected_model = Column(String(100))
    min_threshold = Column(Float)
    status = Column(String(50), default="pending")
    metrics = Column(JSON, default={})
    logs = Column(JSON, default=[]) # Store logs as a JSON array of strings for portable DB compatibility
    bundle_url = Column(String(512))
    plan = Column(Text, nullable=True)

# Helper to automatically construct database tables on module import
Base.metadata.create_all(bind=engine)
