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
    storage_type = Column(String(50), default="local")   # local | s3 | gcs | azure_blob | none
    storage_path = Column(String(1000), default="")      # full physical path or cloud URI
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
            "storage_type": self.storage_type or "local",
            "storage_path": self.storage_path or "",
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


class ModelBuildWf(Base):
    """Parent workflow record — one row per execution of a model approach."""
    __tablename__ = "model_build_wf"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    model_id        = Column(Integer, ForeignKey("models.id"), nullable=True, index=True)
    queue_item_id   = Column(Integer, ForeignKey("model_build_queue.id"), nullable=True, index=True)
    approach_id     = Column(String(100), nullable=False)          # UUID from approaches.json
    status          = Column(String(20), nullable=False, default="started", index=True)
    # started / running / completed / failed
    started_at      = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at        = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    error_message   = Column(Text, default="")

    tasks = relationship("ModelBuildWfTask", back_populates="workflow",
                         cascade="all, delete-orphan", order_by="ModelBuildWfTask.id")

    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "model_id":      self.model_id,
            "queue_item_id": self.queue_item_id,
            "approach_id":   self.approach_id,
            "status":        self.status,
            "started_at":    self.started_at.isoformat() if self.started_at else None,
            "ended_at":      self.ended_at.isoformat()   if self.ended_at   else None,
            "created_at":    self.created_at.isoformat() if self.created_at else None,
            "error_message": self.error_message or "",
            "task_count":    len(self.tasks) if self.tasks else 0,
        }


class ModelBuildWfTask(Base):
    """Child task record — one row per task step inside a workflow run."""
    __tablename__ = "model_build_wf_task"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    wf_id            = Column(Integer, ForeignKey("model_build_wf.id"), nullable=False, index=True)
    task_id          = Column(String(100), nullable=False)   # python class name e.g. Task01ExtractVideoIds
    task_file        = Column(String(200), nullable=False, default="")  # relative path e.g. approach_01/tasks.py
    task_order       = Column(Integer, nullable=False, default=0)
    status           = Column(String(20), nullable=False, default="pending")
    # pending / started / completed / failed / skipped
    started_at       = Column(DateTime, nullable=True)
    ended_at         = Column(DateTime, nullable=True)
    status_updated_at= Column(DateTime, nullable=True,
                               default=lambda: datetime.now(timezone.utc),
                               onupdate=lambda: datetime.now(timezone.utc))
    error_message    = Column(Text, default="")
    output_data      = Column(Text, default="{}")  # JSON dict of task outputs

    workflow = relationship("ModelBuildWf", back_populates="tasks")

    def get_output_data(self) -> dict:
        return json.loads(self.output_data or "{}")

    def to_dict(self) -> dict:
        dur = None
        if self.started_at and self.ended_at:
            dur = round((self.ended_at - self.started_at).total_seconds(), 2)
        return {
            "id":               self.id,
            "wf_id":            self.wf_id,
            "task_id":          self.task_id,
            "task_file":        self.task_file,
            "task_order":       self.task_order,
            "status":           self.status,
            "started_at":       self.started_at.isoformat()        if self.started_at        else None,
            "ended_at":         self.ended_at.isoformat()          if self.ended_at          else None,
            "status_updated_at":self.status_updated_at.isoformat() if self.status_updated_at else None,
            "duration_seconds": dur,
            "error_message":    self.error_message or "",
            "output_data":      self.get_output_data(),
        }


class ModelBuildQueue(Base):
    __tablename__ = "model_build_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(200), nullable=False)
    approach_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    notes = Column(Text, default="")
    context_data = Column(Text, default="{}")
    selected_videos = Column(Text, default="[]")
    selected_sub_models = Column(Text, default="[]")
    publish_as_latest = Column(Boolean, default=False)
    user_id = Column(String(100), nullable=False, default="default")
    created_dt = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    started_dt = Column(DateTime, nullable=True)
    completed_dt = Column(DateTime, nullable=True)
    error_message = Column(Text, default="")

    def to_dict(self) -> dict:
        videos = json.loads(self.selected_videos or "[]")
        return {
            "id": self.id,
            "model_name": self.model_name,
            "approach_type": self.approach_type,
            "status": self.status,
            "notes": self.notes or "",
            "context_data": json.loads(self.context_data or "{}"),
            "selected_videos": videos,
            "selected_videos_count": len(videos),
            "selected_sub_models": json.loads(self.selected_sub_models or "[]"),
            "publish_as_latest": self.publish_as_latest,
            "user_id": self.user_id,
            "created_dt": self.created_dt.isoformat() if self.created_dt else None,
            "updated_dt": self.updated_dt.isoformat() if self.updated_dt else None,
            "started_dt": self.started_dt.isoformat() if self.started_dt else None,
            "completed_dt": self.completed_dt.isoformat() if self.completed_dt else None,
            "error_message": self.error_message or "",
        }


class UserConversation(Base):
    """A user's conversation tied to a model."""
    __tablename__ = "user_conversation"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    uuid              = Column(String(36), nullable=False, unique=True, index=True)
    user_id           = Column(String(100), nullable=False, default="default", index=True)
    conversation_name = Column(String(300), nullable=False)
    model_id          = Column(Integer, ForeignKey("models.id"), nullable=True)
    is_active         = Column(Boolean, nullable=False, default=False)
    settings_json     = Column(Text, default="{}")  # JSON: dist_name, threshold, top_k
    created_at        = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at        = Column(DateTime, nullable=False,
                               default=lambda: datetime.now(timezone.utc),
                               onupdate=lambda: datetime.now(timezone.utc))

    model    = relationship("ModelRecord")
    messages = relationship("UserConversationMessage", back_populates="conversation",
                            cascade="all, delete-orphan", order_by="UserConversationMessage.created_at.desc()")
    history  = relationship("UserConversationHistory", back_populates="conversation",
                            cascade="all, delete-orphan", order_by="UserConversationHistory.snapshot_at.desc()")

    def get_settings(self) -> dict:
        return json.loads(self.settings_json or "{}")

    def to_dict(self) -> dict:
        return {
            "id":                self.id,
            "uuid":              self.uuid,
            "user_id":           self.user_id,
            "conversation_name": self.conversation_name,
            "model_id":          self.model_id,
            "model_name":        self.model.model_name if self.model else None,
            "is_active":         self.is_active,
            "settings":          self.get_settings(),
            "message_count":     len(self.messages) if self.messages else 0,
            "created_at":        self.created_at.isoformat() if self.created_at else None,
            "updated_at":        self.updated_at.isoformat() if self.updated_at else None,
        }


class UserConversationMessage(Base):
    """A single query + results entry inside a conversation."""
    __tablename__ = "user_conversation_message"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("user_conversation.id"), nullable=False, index=True)
    query           = Column(Text, nullable=False)
    results_json    = Column(Text, nullable=False, default="[]")  # JSON array of search results
    created_at      = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("UserConversation", back_populates="messages")

    def get_results(self) -> list:
        return json.loads(self.results_json or "[]")

    def to_dict(self) -> dict:
        return {
            "id":              self.id,
            "conversation_id": self.conversation_id,
            "query":           self.query,
            "results":         self.get_results(),
            "created_at":      self.created_at.isoformat() if self.created_at else None,
        }


class UserConversationHistory(Base):
    """Snapshot clone of user_conversation on every change."""
    __tablename__ = "user_conversation_history"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id   = Column(Integer, ForeignKey("user_conversation.id"), nullable=False, index=True)
    user_id           = Column(String(100), nullable=False)
    conversation_name = Column(String(300), nullable=False)
    model_id          = Column(Integer, nullable=True)
    is_active         = Column(Boolean, nullable=False, default=False)
    snapshot_at       = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("UserConversation", back_populates="history")

    def to_dict(self) -> dict:
        return {
            "id":                self.id,
            "conversation_id":   self.conversation_id,
            "user_id":           self.user_id,
            "conversation_name": self.conversation_name,
            "model_id":          self.model_id,
            "is_active":         self.is_active,
            "snapshot_at":       self.snapshot_at.isoformat() if self.snapshot_at else None,
        }

