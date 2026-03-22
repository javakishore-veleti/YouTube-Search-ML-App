import json
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.app_common.database.db_models import ActivityLog, ModelBuildQueue, ModelRecord, ModelRequest, ModelRequestResource, ModelVersion


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

