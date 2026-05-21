from datetime import datetime

from pydantic import BaseModel, Field


# --- Tag ---

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class TagRead(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)


# --- Note ---

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    tag_ids: list[int] | None = None


class NoteRead(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    tags: list[TagRead] = []

    class Config:
        from_attributes = True


class NotePatch(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    content: str | None = Field(None, min_length=1)
    tag_ids: list[int] | None = None


# --- ActionItem ---

class ActionItemCreate(BaseModel):
    description: str = Field(..., min_length=1)
    note_id: int | None = None


class ActionItemRead(BaseModel):
    id: int
    description: str
    completed: bool
    note_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActionItemPatch(BaseModel):
    description: str | None = Field(None, min_length=1)
    completed: bool | None = None
    note_id: int | None = None


# --- Extract ---

class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1)


class ExtractedItemRead(BaseModel):
    content: str
    category: str
    priority: int

    class Config:
        from_attributes = True
