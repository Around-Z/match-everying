"""Admin API routes — global overview, user management, scenario management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.scenario import AdminStatsResponse, UserResponse
from app.services.auth import require_role
from app.database.mysql import (
    admin_get_stats,
    user_get_all,
    user_get_by_id,
    user_update_role,
    scenario_get_all,
    scenario_delete,
    submission_get_by_scenario,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(admin: dict = Depends(require_role("admin"))):
    """Get global dashboard stats."""
    return AdminStatsResponse(**admin_get_stats())


@router.get("/users")
def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: str = Query(""),
    admin: dict = Depends(require_role("admin")),
):
    """Get paginated user list."""
    users, total = user_get_all(page, limit, role)
    # Strip password_hash from API response
    clean_users = []
    for u in users:
        u = dict(u)
        u.pop("password_hash", None)
        clean_users.append(u)
    return {
        "users": clean_users,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    role_data: dict,
    admin: dict = Depends(require_role("admin")),
):
    """Update a user's role. Body: {"role": "participant|designer|admin"}"""
    new_role = role_data.get("role", "")
    if new_role not in ("participant", "designer", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    user = user_get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_update_role(user_id, new_role)
    return {"status": "ok", "user_id": user_id, "role": new_role}


@router.get("/scenarios")
def get_all_scenarios(
    status: str = Query(""),
    admin: dict = Depends(require_role("admin")),
):
    """Get all scenarios (admin view with full data)."""
    scenarios = scenario_get_all(status or None)
    return {"scenarios": scenarios, "total": len(scenarios)}


@router.delete("/scenarios/{scenario_id}")
def delete_scenario(
    scenario_id: str,
    admin: dict = Depends(require_role("admin")),
):
    """Delete a scenario and all related data."""
    ok = scenario_delete(scenario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"status": "deleted", "scenario_id": scenario_id}
