from pydantic import BaseModel, Field

from fastapi import APIRouter

from ..services.extract import extract_action_items

router = APIRouter(prefix="/extract", tags=["extract"])


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1)


@router.post("/")
def extract(payload: ExtractRequest) -> list[dict[str, str]]:
    return extract_action_items(payload.text)
