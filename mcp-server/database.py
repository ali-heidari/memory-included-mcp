"""SQLAlchemy database models and CRUD operations"""

from sqlalchemy import Column, String, Text, DateTime, LargeBinary, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import uuid
from config import DB_URL

Base = declarative_base()


class Conversation(Base):
    """SQLAlchemy model for storing conversations/memories"""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    conversation_id = Column(String(36), nullable=True, index=True)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    vector_embedding = Column(LargeBinary, nullable=True)
    message_type = Column(String(20), default="user")  # 'user' or 'agent'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite index for efficient user + timestamp queries
    __table_args__ = (Index("idx_user_timestamp", "user_id", "created_at"),)

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "original_text": self.original_text,
            "summary": self.summary,
            "message_type": self.message_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Database:
    """Database connection and CRUD operations"""

    def __init__(self, db_url: str = DB_URL):
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    def add_memory(
        self,
        user_id: str,
        original_text: str,
        summary: str,
        vector_embedding: bytes = None,
        conversation_id: str = None,
        message_type: str = "user",
    ) -> Conversation:
        """Add a new memory to the database"""
        session = self.get_session()
        try:
            memory = Conversation(
                user_id=user_id,
                original_text=original_text,
                summary=summary,
                vector_embedding=vector_embedding,
                conversation_id=conversation_id,
                message_type=message_type,
            )
            session.add(memory)
            session.commit()
            session.refresh(memory)
            return memory
        finally:
            session.close()

    def search_by_user(self, user_id: str, limit: int = 10) -> list[Conversation]:
        """Get all memories for a specific user"""
        session = self.get_session()
        try:
            return (
                session.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .order_by(Conversation.created_at.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    def get_memory_by_id(self, memory_id: str) -> Conversation:
        """Get a specific memory by ID"""
        session = self.get_session()
        try:
            return session.query(Conversation).filter(Conversation.id == memory_id).first()
        finally:
            session.close()

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory"""
        session = self.get_session()
        try:
            memory = session.query(Conversation).filter(Conversation.id == memory_id).first()
            if memory:
                session.delete(memory)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_all_embeddings(self, user_id: str) -> list[tuple]:
        """Get all embeddings for a user (id, embedding)"""
        session = self.get_session()
        try:
            results = (
                session.query(Conversation.id, Conversation.vector_embedding)
                .filter(Conversation.user_id == user_id)
                .filter(Conversation.vector_embedding.isnot(None))
                .all()
            )
            return results
        finally:
            session.close()

    def search_by_conversation_id(self, conversation_id: str) -> list[Conversation]:
        """Get all memories in a conversation"""
        session = self.get_session()
        try:
            return (
                session.query(Conversation)
                .filter(Conversation.conversation_id == conversation_id)
                .order_by(Conversation.created_at)
                .all()
            )
        finally:
            session.close()

    def close(self):
        """Close database connection"""
        self.engine.dispose()


# Global database instance
db = Database()
