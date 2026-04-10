"""
Announcement endpoints for the High School Management System API
"""

from datetime import date
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    """Payload for creating or updating announcements."""

    message: str = Field(..., min_length=5, max_length=400)
    expires_at: str
    starts_at: Optional[str] = None


class AnnouncementResponse(BaseModel):
    """Response model for announcement objects."""

    id: str
    message: str
    starts_at: Optional[str]
    expires_at: str
    created_by: str


def _sanitize_message(message: str) -> str:
    sanitized = " ".join(message.strip().split())
    if len(sanitized) < 5:
        raise HTTPException(status_code=400, detail="Message is too short")
    return sanitized


def _validate_date_range(expires_at: str, starts_at: Optional[str]) -> None:
    try:
        expiration_date = date.fromisoformat(expires_at)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid expiration date format") from exc

    if starts_at:
        try:
            start_date = date.fromisoformat(starts_at)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid start date format") from exc

        if start_date > expiration_date:
            raise HTTPException(status_code=400, detail="Start date cannot be after expiration date")


def _serialize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "message": document["message"],
        "starts_at": document.get("starts_at"),
        "expires_at": document["expires_at"],
        "created_by": document.get("created_by", "unknown")
    }


def _require_signed_user(teacher_username: Optional[str]) -> Dict[str, Any]:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


@router.get("/active", response_model=List[AnnouncementResponse])
def get_active_announcements() -> List[AnnouncementResponse]:
    """Return currently active announcements for public display."""
    today = date.today().isoformat()

    query = {
        "expires_at": {"$gte": today},
        "$or": [
            {"starts_at": None},
            {"starts_at": {"$exists": False}},
            {"starts_at": {"$lte": today}}
        ]
    }

    cursor = announcements_collection.find(query).sort([
        ("expires_at", 1),
        ("starts_at", -1)
    ])

    return [_serialize_announcement(doc) for doc in cursor]


@router.get("", response_model=List[AnnouncementResponse])
def list_announcements(teacher_username: Optional[str] = Query(None)) -> List[AnnouncementResponse]:
    """List all announcements. Requires an authenticated teacher user."""
    _require_signed_user(teacher_username)

    cursor = announcements_collection.find({}).sort([
        ("expires_at", 1),
        ("starts_at", -1)
    ])

    return [_serialize_announcement(doc) for doc in cursor]


@router.post("", response_model=AnnouncementResponse)
def create_announcement(payload: AnnouncementPayload, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement. Requires an authenticated teacher user."""
    teacher = _require_signed_user(teacher_username)

    cleaned_message = _sanitize_message(payload.message)
    _validate_date_range(payload.expires_at, payload.starts_at)

    document = {
        "message": cleaned_message,
        "starts_at": payload.starts_at,
        "expires_at": payload.expires_at,
        "created_by": teacher["username"]
    }

    result = announcements_collection.insert_one(document)
    created = announcements_collection.find_one({"_id": result.inserted_id})

    if not created:
        raise HTTPException(status_code=500, detail="Failed to create announcement")

    return _serialize_announcement(created)


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement. Requires an authenticated teacher user."""
    teacher = _require_signed_user(teacher_username)

    cleaned_message = _sanitize_message(payload.message)
    _validate_date_range(payload.expires_at, payload.starts_at)

    try:
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    result = announcements_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "message": cleaned_message,
                "starts_at": payload.starts_at,
                "expires_at": payload.expires_at,
                "created_by": teacher["username"]
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": object_id})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update announcement")

    return _serialize_announcement(updated)


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, str]:
    """Delete an announcement. Requires an authenticated teacher user."""
    _require_signed_user(teacher_username)

    try:
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    result = announcements_collection.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
