import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from backend.database import get_db
from backend.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationListItem,
    MessageItem
)

COLLECTION_NAME = "conversations"

class ConversationService:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.collection(COLLECTION_NAME)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_conversation(self, conv_in: ConversationCreate, conv_id: Optional[str] = None) -> ConversationResponse:
        now = self._now_iso()
        doc_id = conv_id or str(uuid.uuid4())
        
        # Determine title if not provided
        title = conv_in.title
        if not title:
            if conv_in.messages:
                first_msg = conv_in.messages[0].content
                title = first_msg[:30] + ("..." if len(first_msg) > 30 else "")
            else:
                title = f"새 대화 ({datetime.now().strftime('%m/%d %H:%M')})"

        messages_dict = [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp or now
            }
            for m in conv_in.messages
        ]

        data = {
            "title": title,
            "messages": messages_dict,
            "created_at": now,
            "updated_at": now
        }
        self.collection.document(doc_id).set(data)

        return ConversationResponse(
            id=doc_id,
            title=title,
            messages=[MessageItem(**m) for m in messages_dict],
            created_at=now,
            updated_at=now
        )

    def list_conversations(self) -> List[ConversationListItem]:
        items = []
        for doc in self.collection.stream():
            d = doc.to_dict()
            messages = d.get("messages", [])
            last_msg = messages[-1].get("content") if messages else None
            if last_msg and len(last_msg) > 40:
                last_msg = last_msg[:40] + "..."

            items.append(ConversationListItem(
                id=doc.id,
                title=d.get("title", "대화"),
                message_count=len(messages),
                last_message=last_msg,
                created_at=d.get("created_at"),
                updated_at=d.get("updated_at")
            ))

        items.sort(key=lambda x: x.updated_at or x.created_at or "", reverse=True)
        return items

    def get_conversation(self, conv_id: str) -> Optional[ConversationResponse]:
        doc = self.collection.document(conv_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        messages = [MessageItem(**m) for m in d.get("messages", [])]
        return ConversationResponse(
            id=doc.id,
            title=d.get("title", "대화"),
            messages=messages,
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at")
        )

    def add_message(self, conv_id: str, role: str, content: str) -> ConversationResponse:
        now = self._now_iso()
        doc_ref = self.collection.document(conv_id)
        doc = doc_ref.get()

        new_msg = {
            "role": role,
            "content": content,
            "timestamp": now
        }

        if not doc.exists:
            title = content[:30] + ("..." if len(content) > 30 else "")
            data = {
                "title": title,
                "messages": [new_msg],
                "created_at": now,
                "updated_at": now
            }
            doc_ref.set(data)
            return ConversationResponse(
                id=conv_id,
                title=title,
                messages=[MessageItem(**new_msg)],
                created_at=now,
                updated_at=now
            )
        else:
            d = doc.to_dict()
            messages = d.get("messages", [])
            messages.append(new_msg)
            title = d.get("title") or (content[:30] + ("..." if len(content) > 30 else ""))
            doc_ref.update({
                "messages": messages,
                "title": title,
                "updated_at": now
            })
            return ConversationResponse(
                id=conv_id,
                title=title,
                messages=[MessageItem(**m) for m in messages],
                created_at=d.get("created_at"),
                updated_at=now
            )

    def delete_conversation(self, conv_id: str) -> bool:
        doc_ref = self.collection.document(conv_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        doc_ref.delete()
        return True
