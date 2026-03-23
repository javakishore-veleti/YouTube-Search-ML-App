import json
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.app_common.database.db_models import (
    ActivityLog, ModelBuildQueue, ModelBuildWf, ModelBuildWfTask,
    ModelRecord, ModelRequest, ModelRequestResource, ModelVersion,
    UserConversation, UserConversationHistory, UserConversationMessage,
)


class QueueRepository:
    """CRUD for the model build queue."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def enqueue(self, model_name: str, approach_type: str, selected_videos: list,
                notes: str = "", context_data: str = "{}", publish_as_latest: bool = False,
                user_id: str = "default", selected_sub_models: Optional[list] = None) -> ModelBuildQueue:
        item = ModelBuildQueue(
            model_name=model_name,
            approach_type=approach_type,
            selected_videos=json.dumps(selected_videos),
            selected_sub_models=json.dumps(selected_sub_models or []),
            notes=notes,
            context_data=context_data if context_data else "{}",
            publish_as_latest=publish_as_latest,
            user_id=user_id,
            status="pending",
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def list_paginated(self, page: int = 1, page_size: int = 10, status_filter: Optional[str] = None) -> dict:
        q = self.session.query(ModelBuildQueue)
        if status_filter:
            q = q.filter(ModelBuildQueue.status == status_filter)
        total = q.count()
        rows = (
            q.order_by(ModelBuildQueue.created_dt.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "items": [r.to_dict() for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, -(-total // page_size)),
        }

    def get_by_id(self, item_id: int) -> Optional[ModelBuildQueue]:
        return self.session.query(ModelBuildQueue).filter_by(id=item_id).first()

    def pick_next_pending(self) -> Optional[ModelBuildQueue]:
        item = (
            self.session.query(ModelBuildQueue)
            .filter_by(status="pending")
            .order_by(ModelBuildQueue.created_dt.asc())
            .first()
        )
        if item:
            item.status = "in_progress"
            item.started_dt = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(item)
        return item

    def mark_completed(self, item_id: int) -> None:
        item = self.get_by_id(item_id)
        if item:
            item.status = "completed"
            item.completed_dt = datetime.now(timezone.utc)
            self.session.commit()

    def mark_failed(self, item_id: int, error_message: str) -> None:
        item = self.get_by_id(item_id)
        if item:
            item.status = "failed"
            item.completed_dt = datetime.now(timezone.utc)
            item.error_message = error_message
            self.session.commit()


class ActivityRepository:
    """Paginated CRUD for activity logs — designed for 100K+ rows."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, name: str, status: str = "info") -> ActivityLog:
        entry = ActivityLog(name=name, status=status)
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def list_paginated(self, page: int = 1, page_size: int = 10) -> dict:
        total = self.session.query(ActivityLog).count()
        rows = (
            self.session.query(ActivityLog)
            .order_by(ActivityLog.created_dt.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "items": [r.to_dict() for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, -(-total // page_size)),  # ceil division
        }


class ModelRepository:
    """CRUD operations for models and model versions in SQLite."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ── Models ────────────────────────────────────────────────────────────

    def create_model(
        self,
        model_name: str,
        approach_type: str,
        user_id: str = "default",
        input_criteria: Optional[dict] = None,
        output_results: Optional[dict] = None,
    ) -> ModelRecord:
        record = ModelRecord(
            user_id=user_id,
            model_name=model_name,
            model_approach_type=approach_type,
            input_criteria=json.dumps(input_criteria or {}),
            output_results=json.dumps(output_results or {}),
            latest_version="1.0.0",
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def list_models(self) -> List[ModelRecord]:
        return self.session.query(ModelRecord).order_by(ModelRecord.updated_dt.desc()).all()

    def get_model(self, model_id: int) -> Optional[ModelRecord]:
        return self.session.query(ModelRecord).filter_by(id=model_id).first()

    def update_model(
        self,
        model_id: int,
        output_results: Optional[dict] = None,
        latest_version: Optional[str] = None,
    ) -> Optional[ModelRecord]:
        record = self.get_model(model_id)
        if not record:
            return None
        if output_results is not None:
            record.output_results = json.dumps(output_results)
        if latest_version is not None:
            record.latest_version = latest_version
        record.updated_dt = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(record)
        return record

    # ── Versions ──────────────────────────────────────────────────────────

    def create_version(
        self,
        model_id: int,
        version: str,
        input_criteria: Optional[dict] = None,
        output_criteria: Optional[dict] = None,
        model_location: str = "",
    ) -> ModelVersion:
        ver = ModelVersion(
            model_id=model_id,
            version=version,
            input_criteria=json.dumps(input_criteria or {}),
            output_criteria=json.dumps(output_criteria or {}),
            model_location=model_location,
        )
        self.session.add(ver)
        self.session.commit()
        self.session.refresh(ver)
        return ver

    def get_versions(self, model_id: int) -> List[ModelVersion]:
        return (
            self.session.query(ModelVersion)
            .filter_by(model_id=model_id)
            .order_by(ModelVersion.created_dt.desc())
            .all()
        )

    # ── Model Requests ────────────────────────────────────────────────────

    def create_request(
        self,
        model_id: int,
        resources: List[dict],
    ) -> ModelRequest:
        req = ModelRequest(
            model_id=model_id,
            model_approach_status="pending",
        )
        self.session.add(req)
        self.session.flush()  # get req.id

        for res in resources:
            resource = ModelRequestResource(
                model_request_id=req.id,
                resource_type=res.get("resource_type", "youtube"),
                resource_type_id=res.get("resource_type_id", ""),
                resource_metadata_json=json.dumps(res.get("metadata", {})),
            )
            self.session.add(resource)

        self.session.commit()
        self.session.refresh(req)
        return req

    def get_requests(self, model_id: int) -> List[ModelRequest]:
        return (
            self.session.query(ModelRequest)
            .filter_by(model_id=model_id)
            .order_by(ModelRequest.created_dt.desc())
            .all()
        )

    def get_request(self, request_id: int) -> Optional[ModelRequest]:
        return self.session.query(ModelRequest).filter_by(id=request_id).first()

    def get_request_resources(self, request_id: int) -> List[ModelRequestResource]:
        return (
            self.session.query(ModelRequestResource)
            .filter_by(model_request_id=request_id)
            .all()
        )

    def update_request_status(self, request_id: int, status: str) -> Optional[ModelRequest]:
        req = self.get_request(request_id)
        if not req:
            return None
        req.model_approach_status = status
        req.updated_dt = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(req)
        return req


class WorkflowRepository:
    """CRUD for model_build_wf (parent) and model_build_wf_task (child)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ── Workflow ──────────────────────────────────────────────────────────

    def create_wf(self, approach_id: str, model_id: Optional[int] = None,
                  queue_item_id: Optional[int] = None) -> ModelBuildWf:
        now = datetime.now(timezone.utc)
        wf = ModelBuildWf(
            approach_id=approach_id,
            model_id=model_id,
            queue_item_id=queue_item_id,
            status="started",
            started_at=now,
            created_at=now,
        )
        self.session.add(wf)
        self.session.commit()
        self.session.refresh(wf)
        return wf

    def update_wf_status(self, wf_id: int, status: str,
                         error: str = "") -> Optional[ModelBuildWf]:
        wf = self.session.query(ModelBuildWf).filter_by(id=wf_id).first()
        if not wf:
            return None
        wf.status = status
        wf.ended_at = datetime.now(timezone.utc)
        wf.error_message = error
        self.session.commit()
        return wf

    def link_wf_model(self, wf_id: int, model_id: int) -> None:
        wf = self.session.query(ModelBuildWf).filter_by(id=wf_id).first()
        if wf:
            wf.model_id = model_id
            self.session.commit()

    def list_wf_for_model(self, model_id: int) -> List[ModelBuildWf]:
        return (
            self.session.query(ModelBuildWf)
            .filter_by(model_id=model_id)
            .order_by(ModelBuildWf.started_at.desc())
            .all()
        )

    def get_wf(self, wf_id: int) -> Optional[ModelBuildWf]:
        return self.session.query(ModelBuildWf).filter_by(id=wf_id).first()

    def list_all_wf(self, page: int = 1, page_size: int = 10,
                    status_filter: Optional[str] = None) -> dict:
        q = self.session.query(ModelBuildWf)
        if status_filter:
            q = q.filter(ModelBuildWf.status == status_filter)
        total = q.count()
        rows = (
            q.order_by(ModelBuildWf.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "items": [r.to_dict() for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, -(-total // page_size)),
        }

    def get_task(self, task_id: int) -> Optional[ModelBuildWfTask]:
        return self.session.query(ModelBuildWfTask).filter_by(id=task_id).first()

    # ── Tasks ────────────────────────────────────────────────────────────

    def create_task(self, wf_id: int, task_id: str, task_file: str,
                    task_order: int) -> ModelBuildWfTask:
        now = datetime.now(timezone.utc)
        t = ModelBuildWfTask(
            wf_id=wf_id,
            task_id=task_id,
            task_file=task_file,
            task_order=task_order,
            status="pending",
            status_updated_at=now,
        )
        self.session.add(t)
        self.session.commit()
        self.session.refresh(t)
        return t

    def start_task(self, task_row_id: int) -> Optional[ModelBuildWfTask]:
        t = self.session.query(ModelBuildWfTask).filter_by(id=task_row_id).first()
        if not t:
            return None
        now = datetime.now(timezone.utc)
        t.status = "started"
        t.started_at = now
        t.status_updated_at = now
        self.session.commit()
        return t

    def finish_task(self, task_row_id: int, status: str,
                    error: str = "",
                    output_data: Optional[dict] = None) -> Optional[ModelBuildWfTask]:
        t = self.session.query(ModelBuildWfTask).filter_by(id=task_row_id).first()
        if not t:
            return None
        now = datetime.now(timezone.utc)
        t.status = status
        t.ended_at = now
        t.status_updated_at = now
        t.error_message = error
        if output_data:
            import json as _json
            t.output_data = _json.dumps(output_data)
        self.session.commit()
        return t

    def list_tasks(self, wf_id: int, page: int = 1,
                   page_size: int = 10) -> dict:
        q = (self.session.query(ModelBuildWfTask)
             .filter_by(wf_id=wf_id)
             .order_by(ModelBuildWfTask.task_order))
        total = q.count()
        rows = q.offset((page - 1) * page_size).limit(page_size).all()
        return {
            "items": [r.to_dict() for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, -(-total // page_size)),
        }


class ConversationRepository:
    """CRUD for user_conversation with history snapshotting."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _clone_to_history(self, conv: UserConversation) -> None:
        snapshot = UserConversationHistory(
            conversation_id=conv.id,
            user_id=conv.user_id,
            conversation_name=conv.conversation_name,
            model_id=conv.model_id,
            is_active=conv.is_active,
            snapshot_at=datetime.now(timezone.utc),
        )
        self.session.add(snapshot)

    def create(self, user_id: str, name: str, model_id: Optional[int] = None) -> UserConversation:
        import uuid as _uuid
        # deactivate other conversations for this user
        self.session.query(UserConversation).filter_by(user_id=user_id, is_active=True).update(
            {"is_active": False, "updated_at": datetime.now(timezone.utc)}
        )
        conv = UserConversation(
            uuid=str(_uuid.uuid4()),
            user_id=user_id,
            conversation_name=name,
            model_id=model_id,
            is_active=True,
        )
        self.session.add(conv)
        self.session.flush()
        self._clone_to_history(conv)
        self.session.commit()
        self.session.refresh(conv)
        return conv

    def list_for_user(self, user_id: str) -> List[UserConversation]:
        return (
            self.session.query(UserConversation)
            .filter_by(user_id=user_id)
            .order_by(UserConversation.updated_at.desc())
            .all()
        )

    def get(self, conversation_id: int) -> Optional[UserConversation]:
        return self.session.query(UserConversation).filter_by(id=conversation_id).first()

    def get_active(self, user_id: str) -> Optional[UserConversation]:
        return (
            self.session.query(UserConversation)
            .filter_by(user_id=user_id, is_active=True)
            .first()
        )

    def set_active(self, conversation_id: int, user_id: str) -> Optional[UserConversation]:
        self.session.query(UserConversation).filter_by(user_id=user_id, is_active=True).update(
            {"is_active": False, "updated_at": datetime.now(timezone.utc)}
        )
        conv = self.get(conversation_id)
        if not conv:
            return None
        conv.is_active = True
        conv.updated_at = datetime.now(timezone.utc)
        self._clone_to_history(conv)
        self.session.commit()
        self.session.refresh(conv)
        return conv

    def update(self, conversation_id: int, name: Optional[str] = None,
               model_id: Optional[int] = None) -> Optional[UserConversation]:
        conv = self.get(conversation_id)
        if not conv:
            return None
        if name is not None:
            conv.conversation_name = name
        if model_id is not None:
            conv.model_id = model_id
        conv.updated_at = datetime.now(timezone.utc)
        self._clone_to_history(conv)
        self.session.commit()
        self.session.refresh(conv)
        return conv

    def delete(self, conversation_id: int) -> bool:
        conv = self.get(conversation_id)
        if not conv:
            return False
        self.session.delete(conv)
        self.session.commit()
        return True

    # ── Messages ───────────────────────────────────────────────────────
    def add_message(self, conversation_id: int, query: str,
                    results: list) -> Optional[UserConversationMessage]:
        conv = self.get(conversation_id)
        if not conv:
            return None
        msg = UserConversationMessage(
            conversation_id=conversation_id,
            query=query,
            results_json=json.dumps(results),
        )
        self.session.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(msg)
        return msg

    def list_messages(self, conversation_id: int, page: int = 1,
                      page_size: int = 25) -> dict:
        q = (self.session.query(UserConversationMessage)
             .filter_by(conversation_id=conversation_id)
             .order_by(UserConversationMessage.created_at.desc()))
        total = q.count()
        rows = q.offset((page - 1) * page_size).limit(page_size).all()
        return {
            "items": [r.to_dict() for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, -(-total // page_size)),
        }

