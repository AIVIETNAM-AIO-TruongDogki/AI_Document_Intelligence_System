import uuid
from typing import Any
from sqlalchemy.orm import Session
from app.db.models import ChatSessionModel, ChatMessageModel


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(self, title: str = "Hội thoại mới") -> ChatSessionModel:
        session = ChatSessionModel(id=f"session_{uuid.uuid4()}", title=title)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: list[dict[str, Any]] | None = None,
        tokens_used: dict[str, int] | None = None,
    ) -> ChatMessageModel:
        message = ChatMessageModel(
            id=f"msg_{uuid.uuid4()}",
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
            tokens_used=tokens_used,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_session_history(self, session_id: str) -> list[ChatMessageModel]:
        return (
            self.db.query(ChatMessageModel)
            .filter(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
            .all()
        )

    def get_session(self, session_id: str) -> ChatSessionModel | None:
        return (
            self.db.query(ChatSessionModel)
            .filter(ChatSessionModel.id == session_id)
            .first()
        )

    def list_sessions(self) -> list[ChatSessionModel]:
        return (
            self.db.query(ChatSessionModel)
            .order_by(ChatSessionModel.updated_at.desc())
            .all()
        )

    def delete_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        self.db.delete(session)
        self.db.commit()
        return True

