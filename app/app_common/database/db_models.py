import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class ModelRecord(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, default="default")
    model_name = Column(String(200), nullable=False)
    model_approach_type = Column(String(50), nullable=False)
    created_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    input_criteria = Column(Text, default="{}")
    output_results = Column(Text, default="{}")
    latest_version = Column(String(50), default="1.0.0")

    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
    requests = relationship("ModelRequest", back_populates="model", cascade="all, delete-orphan")

    def get_input_criteria(self) -> dict:
        return json.loads(self.input_criteria or "{}")

    def get_output_results(self) -> dict:
        return json.loads(self.output_results or "{}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "model_name": self.model_name,
            "model_approach_type": self.model_approach_type,
            "created_dt": self.created_dt.isoformat() if self.created_dt else None,
            "updated_dt": self.updated_dt.isoformat() if self.updated_dt else None,
            "input_criteria": self.get_input_criteria(),
            "output_results": self.get_output_results(),
            "latest_version": self.latest_version,
        }


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    version = Column(String(50), nullable=False)
    input_criteria = Column(Text, default="{}")
    output_criteria = Column(Text, default="{}")
    model_location = Column(String(500), default="")
    created_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    model = relationship("ModelRecord", back_populates="versions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "model_id": self.model_id,
            "version": self.version,
            "input_criteria": json.loads(self.input_criteria or "{}"),
            "output_criteria": json.loads(self.output_criteria or "{}"),
            "model_location": self.model_location,
            "created_dt": self.created_dt.isoformat() if self.created_dt else None,
        }


class ModelRequest(Base):
    __tablename__ = "model_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    request_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    model_approach_status = Column(String(30), default="pending")  # pending, running, completed, failed
    created_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    model = relationship("ModelRecord", back_populates="requests")
    resources = relationship("ModelRequestResource", back_populates="request", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "model_id": self.model_id,
            "request_date": self.request_date.isoformat() if self.request_date else None,
            "model_approach_status": self.model_approach_status,
            "resource_count": len(self.resources) if self.resources else 0,
            "created_dt": self.created_dt.isoformat() if self.created_dt else None,
            "updated_dt": self.updated_dt.isoformat() if self.updated_dt else None,
        }


class ModelRequestResource(Base):
    __tablename__ = "model_request_resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_request_id = Column(Integer, ForeignKey("model_requests.id"), nullable=False)
    resource_type = Column(String(50), nullable=False, default="youtube")  # youtube, etc.
    resource_type_id = Column(String(200), nullable=False)  # e.g. YouTube video ID
    resource_metadata_json = Column(Text, default="{}")  # JSON: {url, title, channel, ...}
    created_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    request = relationship("ModelRequest", back_populates="resources")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "model_request_id": self.model_request_id,
            "resource_type": self.resource_type,
            "resource_type_id": self.resource_type_id,
            "resource_metadata": json.loads(self.resource_metadata_json or "{}"),
            "created_dt": self.created_dt.isoformat() if self.created_dt else None,
        }


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    status = Column(String(50), nullable=False, default="info")  # info, success, warning, error, pending, completed, failed
    created_dt = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "datetime": self.created_dt.isoformat() if self.created_dt else None,
        }


class ModelBuildQueue(Base):
    __tablename__ = "model_build_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(200), nullable=False)
    approach_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, in_progress, completed, failed
    notes = Column(Text, default="")  # user-facing notes
    context_data = Column(Text, default="{}")  # JSON — extra context for model improvement
    selected_videos = Column(Text, default="[]")  # JSON — list of video dicts
    publish_as_latest = Column(Boolean, default=False)
    user_id = Column(String(100), nullable=False, default="default")
    created_dt = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    started_dt = Column(DateTime, nullable=True)
    completed_dt = Column(DateTime, nullable=True)
    error_message = Column(Text, default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "model_name": self.model_name,
            "approach_type": self.approach_type,
            "status": self.status,
            "notes": self.notes or "",
            "context_data": json.loads(self.context_data or "{}"),
            "selected_videos_count": len(json.loads(self.selected_videos or "[]")),
            "publish_as_latest": self.publish_as_latest,
            "user_id": self.user_id,
            "created_dt": self.created_dt.isoformat() if self.created_dt else None,
            "updated_dt": self.updated_dt.isoformat() if self.updated_dt else None,
            "started_dt": self.started_dt.isoformat() if self.started_dt else None,
            "completed_dt": self.completed_dt.isoformat() if self.completed_dt else None,
            "error_message": self.error_message or "",
        }


