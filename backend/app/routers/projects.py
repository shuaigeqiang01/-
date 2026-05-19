from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActionItem, Note, Project
from ..schemas import (
    ActionItemRead,
    NoteRead,
    ProjectCreate,
    ProjectPatch,
    ProjectRead,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=0, le=200),
    sort: str = Query("-created_at"),
) -> list[ProjectRead]:
    sort_field = sort.lstrip("-")
    order_fn = desc if sort.startswith("-") else asc
    if hasattr(Project, sort_field):
        order_by = order_fn(getattr(Project, sort_field))
    else:
        order_by = desc(Project.created_at)
    stmt = select(Project).order_by(order_by).offset(skip).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [ProjectRead.model_validate(row) for row in rows]


@router.post("/", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    project = Project(name=payload.name, description=payload.description)
    db.add(project)
    db.flush()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectRead:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
def patch_project(project_id: int, payload: ProjectPatch, db: Session = Depends(get_db)) -> ProjectRead:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    db.add(project)
    db.flush()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)


@router.get("/{project_id}/notes", response_model=list[NoteRead])
def list_project_notes(
    project_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=0, le=200),
) -> list[NoteRead]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    stmt = select(Note).where(Note.project_id == project_id).offset(skip).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [NoteRead.model_validate(row) for row in rows]


@router.get("/{project_id}/action-items", response_model=list[ActionItemRead])
def list_project_action_items(
    project_id: int,
    db: Session = Depends(get_db),
    completed: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=0, le=200),
) -> list[ActionItemRead]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    stmt = select(ActionItem).where(ActionItem.project_id == project_id)
    if completed is not None:
        stmt = stmt.where(ActionItem.completed.is_(completed))
    stmt = stmt.offset(skip).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [ActionItemRead.model_validate(row) for row in rows]
