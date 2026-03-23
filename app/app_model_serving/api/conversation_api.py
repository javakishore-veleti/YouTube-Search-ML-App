import json
import logging

from fastapi import Request

from app.app_common.database.db_engine import SessionLocal
from app.app_common.database.db_repo import ConversationRepository
from app.app_common.dtos.init_dtos import InitDTO
from app.app_model_serving import conversation_storage

logger = logging.getLogger(__name__)


class ConversationAPI:

    def list_conversations(self, request: Request) -> list:
        user_id = request.query_params.get("user_id", "default")
        session = SessionLocal()
        try:
            return [c.to_dict() for c in ConversationRepository(session).list_for_user(user_id)]
        finally:
            session.close()

    def get_active(self, request: Request) -> dict:
        user_id = request.query_params.get("user_id", "default")
        session = SessionLocal()
        try:
            conv = ConversationRepository(session).get_active(user_id)
            return conv.to_dict() if conv else {}
        finally:
            session.close()

    def get_conversation(self, request: Request) -> dict:
        cid = int(request.path_params["id"])
        session = SessionLocal()
        try:
            conv = ConversationRepository(session).get(cid)
            return conv.to_dict() if conv else {"error": "Not found"}
        finally:
            session.close()

    async def create_conversation(self, request: Request) -> dict:
        body = await request.json()
        user_id = body.get("user_id", "default")
        name = body.get("conversation_name", "")
        model_id = body.get("model_id")
        if not name:
            return {"error": "conversation_name is required"}
        session = SessionLocal()
        try:
            conv = ConversationRepository(session).create(
                user_id=user_id, name=name, model_id=model_id,
            )
            return {"status": "created", "conversation": conv.to_dict()}
        finally:
            session.close()

    async def update_conversation(self, request: Request) -> dict:
        cid = int(request.path_params["id"])
        body = await request.json()
        name = body.get("conversation_name")
        model_id = body.get("model_id")
        session = SessionLocal()
        try:
            conv = ConversationRepository(session).update(cid, name=name, model_id=model_id)
            if not conv:
                return {"error": "Not found"}
            return {"status": "updated", "conversation": conv.to_dict()}
        finally:
            session.close()

    async def activate_conversation(self, request: Request) -> dict:
        cid = int(request.path_params["id"])
        body = await request.json() if request.headers.get("content-length", "0") != "0" else {}
        user_id = body.get("user_id", "default")
        session = SessionLocal()
        try:
            conv = ConversationRepository(session).set_active(cid, user_id)
            if not conv:
                return {"error": "Not found"}
            return {"status": "activated", "conversation": conv.to_dict()}
        finally:
            session.close()

    def delete_conversation(self, request: Request) -> dict:
        cid = int(request.path_params["id"])
        session = SessionLocal()
        try:
            repo = ConversationRepository(session)
            conv = repo.get(cid)
            conv_uuid = conv.uuid if conv else None
            ok = repo.delete(cid)
            if ok and conv_uuid:
                conversation_storage.delete_files(conv_uuid)
            return {"status": "deleted"} if ok else {"error": "Not found"}
        finally:
            session.close()

    # ── Messages ───────────────────────────────────────────────────
    async def add_message(self, request: Request) -> dict:
        cid = int(request.path_params["id"])
        body = await request.json()
        query = body.get("query", "")
        results = body.get("results", [])
        if not query:
            return {"error": "query is required"}

        session = SessionLocal()
        try:
            repo = ConversationRepository(session)
            msg = repo.add_message(cid, query, results)
            if not msg:
                return {"error": "Conversation not found"}

            # rebuild JSON files on disk
            conv = repo.get(cid)
            if conv:
                all_msgs = repo.list_messages(cid, page=1, page_size=1000)
                conversation_storage.append_message(conv.uuid, msg.to_dict(), all_msgs["items"])

            return {"status": "saved", "message": msg.to_dict()}
        finally:
            session.close()

    def list_messages(self, request: Request) -> dict:
        cid = int(request.path_params["id"])
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 25))
        page_size = max(1, min(page_size, 50))
        session = SessionLocal()
        try:
            return ConversationRepository(session).list_messages(cid, page=page, page_size=page_size)
        finally:
            session.close()


class Initializer:
    def initialize(self, dto: InitDTO) -> None:
        handler = ConversationAPI()
        app = dto.app
        app.add_api_route("/conversations",               endpoint=handler.list_conversations, methods=["GET"])
        app.add_api_route("/conversations/active",        endpoint=handler.get_active, methods=["GET"])
        app.add_api_route("/conversations",               endpoint=handler.create_conversation, methods=["POST"])
        app.add_api_route("/conversations/{id}",          endpoint=handler.get_conversation, methods=["GET"])
        app.add_api_route("/conversations/{id}",          endpoint=handler.update_conversation, methods=["PUT"])
        app.add_api_route("/conversations/{id}",          endpoint=handler.delete_conversation, methods=["DELETE"])
        app.add_api_route("/conversations/{id}/activate", endpoint=handler.activate_conversation, methods=["PUT"])
        app.add_api_route("/conversations/{id}/messages", endpoint=handler.list_messages, methods=["GET"])
        app.add_api_route("/conversations/{id}/messages", endpoint=handler.add_message, methods=["POST"])
