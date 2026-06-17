"""Submission (form filling) API routes."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from app.models.scenario import SubmissionCreate, SubmissionResponse
from app.database import mysql as db
from app.services.matching import embed_and_store_submission
from app.services.auth import get_current_user, require_auth

logger = logging.getLogger("matching.submissions")

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.get("/scenario/{scenario_id}", response_model=list[SubmissionResponse])
def list_submissions(
    scenario_id: str,
    user: dict = Depends(require_auth),
):
    """List submissions for a scenario. Admin sees all; creator sees all; others see only their own."""
    scenario = db.scenario_get_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    all_subs = db.submission_get_by_scenario(scenario_id)
    # Admin or the scenario creator can see all submissions
    if user["role"] == "admin" or scenario.get("creator_id") == user["id"]:
        return all_subs
    return [s for s in all_subs if s["user_id"] == user["id"]]


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: str,
    user: dict = Depends(require_auth),
):
    """Get a single submission by ID. Only owner or admin can view."""
    sub = db.submission_get_by_id(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user["role"] != "admin" and sub["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="只能查看自己的提交")
    return sub


@router.post("", response_model=SubmissionResponse, status_code=201)
async def create_submission(
    data: SubmissionCreate,
    background_tasks: BackgroundTasks,
    user: Optional[dict] = Depends(get_current_user),
):
    """Create a new submission (fill a matching form).

    The submission is saved and embedding + Milvus upsert is done
    in the background. If authenticated, user_id is linked to the account.
    """
    # Validate scenario exists
    scenario = db.scenario_get_by_id(data.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scenario["status"] != "active":
        raise HTTPException(status_code=400, detail="Scenario is not active")

    # Validate form data against schema
    _validate_form_data(data.form_data, scenario["form_schema"])

    # Auto-inject user tags into form_data for cross-scenario matching
    form_data = dict(data.form_data)
    if user and user.get("tags"):
        form_data["_user_tags"] = user["tags"]

    # Create submission (without embedding yet)
    sub_id = db.submission_create({
        "scenario_id": data.scenario_id,
        "user_id": user["id"] if user else "anonymous",
        "form_data": form_data,
        "embedding_vector": None,
    })
    if not user:
        logger.warning("Submission %s created without authentication — user_id=anonymous. "
                       "Frontend may be missing Authorization header.", sub_id)

    # Run embedding + vector store upsert in background
    background_tasks.add_task(
        embed_and_store_submission,
        sub_id,
        data.form_data,
        scenario["match_config"].get("embedding_fields", []),
        data.scenario_id,
    )

    return db.submission_get_by_id(sub_id)


def _validate_form_data(form_data: dict, form_schema: dict):
    """Validate form data against the scenario's form schema."""
    fields = form_schema.get("fields", [])
    for field in fields:
        key = field["key"]
        required = field.get("required", True)

        if required and (key not in form_data or form_data[key] is None or form_data[key] == ""):
            raise HTTPException(
                status_code=400,
                detail=f"Required field '{field['label']}' is missing or empty",
            )

        if key in form_data and form_data[key] is not None:
            value = form_data[key]
            field_type = field["type"]

            if field_type == "number" and not isinstance(value, (int, float)):
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field['label']}' must be a number",
                )
            if field_type == "select" and "options" in field:
                if value not in field["options"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Field '{field['label']}' value not in allowed options",
                    )
            if field_type == "multi_select" and "options" in field:
                if isinstance(value, list):
                    for v in value:
                        if v not in field["options"]:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Field '{field['label']}' value '{v}' not in allowed options",
                            )
