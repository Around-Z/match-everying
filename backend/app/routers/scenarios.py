"""Scenario management API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.models.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioStats,
    GenerateScenarioRequest,
    GenerateScenarioResponse,
)
from app.database import mysql as db
from app.services.llm import generate_scenario_config
from app.services.auth import get_current_user, require_auth

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioResponse])
def list_scenarios(status: str | None = None):
    """List all scenarios, optionally filtered by status."""
    scenarios = db.scenario_get_all(status)
    result = []
    for s in scenarios:
        s["submission_count"] = db.scenario_get_submission_count(s["id"])
        result.append(s)
    return result


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: str):
    """Get a single scenario by ID."""
    scenario = db.scenario_get_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario["submission_count"] = db.scenario_get_submission_count(scenario_id)
    return scenario


@router.post("", response_model=ScenarioResponse, status_code=201)
def create_scenario(
    data: ScenarioCreate,
    user: Optional[dict] = Depends(get_current_user),
):
    """Create a new matching scenario manually. Links to authenticated user if logged in."""
    # Validate: must have a contact field
    fields = data.form_schema.fields
    has_contact = any(f.type == "contact" for f in fields)
    if not has_contact:
        raise HTTPException(
            status_code=400,
            detail="Every scenario must include a 'contact' field (type=contact) for participants to provide contact info.",
        )
    sid = db.scenario_create({
        "creator_id": user["id"] if user else "anonymous",
        "name": data.name,
        "description": data.description,
        "form_schema": data.form_schema.model_dump(),
        "match_config": data.match_config.model_dump(),
        "ui_config": data.ui_config.model_dump(),
        "status": data.status.value,
    })
    scenario = db.scenario_get_by_id(sid)
    scenario["submission_count"] = 0
    return scenario


@router.put("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: str,
    data: ScenarioUpdate,
    user: dict = Depends(require_auth),
):
    """Update an existing scenario. Only the creator or admin can update."""
    scenario = db.scenario_get_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if user["role"] != "admin" and scenario["creator_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="只有场景创建者或管理员才能修改此场景")

    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    ok = db.scenario_update(scenario_id, update_data)
    if not ok:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario = db.scenario_get_by_id(scenario_id)
    scenario["submission_count"] = db.scenario_get_submission_count(scenario_id)
    return scenario


@router.delete("/{scenario_id}", status_code=204)
def delete_scenario(
    scenario_id: str,
    user: dict = Depends(require_auth),
):
    """Delete a scenario and all its submissions. Only the creator or admin can delete."""
    scenario = db.scenario_get_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if user["role"] != "admin" and scenario["creator_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="只有场景创建者或管理员才能删除此场景")

    ok = db.scenario_delete(scenario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Scenario not found")


@router.post("/generate", response_model=GenerateScenarioResponse)
async def generate_scenario(request: GenerateScenarioRequest):
    """Generate a scenario configuration from natural language using DeepSeek API."""
    try:
        config = await generate_scenario_config(request.prompt)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate scenario: {str(e)}",
        )


@router.get("/{scenario_id}/stats", response_model=ScenarioStats)
def get_scenario_stats(scenario_id: str):
    """Get statistics for a scenario."""
    scenario = db.scenario_get_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    submission_count = db.scenario_get_submission_count(scenario_id)
    # Count matches for this scenario
    match_count = 0
    submissions = db.submission_get_by_scenario(scenario_id)
    for sub in submissions:
        matches = db.match_result_get_by_submission(sub["id"])
        match_count += len(matches)

    return ScenarioStats(
        scenario_id=scenario_id,
        scenario_name=scenario["name"],
        submission_count=submission_count,
        match_count=match_count,
        status=scenario["status"],
    )
