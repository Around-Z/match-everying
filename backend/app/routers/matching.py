"""Matching API routes — triggers matching and retrieves results with privacy control."""

from fastapi import APIRouter, HTTPException, Depends
from app.models.scenario import MatchResponse, MatchResultItem
from app.database import mysql as db
from app.services.matching import run_matching
from app.services.auth import require_auth, get_current_user
from app.config import MATCH_VISIBILITY_THRESHOLD
from typing import Optional

router = APIRouter(prefix="/api/matching", tags=["matching"])

CONTACT_HIDDEN = "*** (visible when match score > 50%)"
CONTACT_FIELD_KEY = "contact"


def _apply_privacy(matches: list[dict], user_role: str, owner_submission_id: str) -> list[dict]:
    """Apply privacy rules to match results.

    - Admin: see everything
    - Regular user: only see matches with similarity_score > threshold;
      contact field hidden unless it's their own submission.
    """
    if user_role == "admin":
        return matches

    filtered = []
    for m in matches:
        score = m.get("similarity_score", 0)
        if score < MATCH_VISIBILITY_THRESHOLD:
            continue
        # Hide contact info for non-owners
        form_data = m.get("matched_form_data", {})
        if CONTACT_FIELD_KEY in form_data:
            if m.get("submission_id") != owner_submission_id:
                form_data = dict(form_data)
                form_data[CONTACT_FIELD_KEY] = CONTACT_HIDDEN
                m = dict(m)
                m["matched_form_data"] = form_data
        filtered.append(m)
    return filtered


@router.post("/run/{submission_id}", response_model=MatchResponse)
async def run_matching_for_submission(
    submission_id: str,
    user: dict = Depends(require_auth),
):
    """Run the matching pipeline for a submission (auth required, ownership checked)."""
    submission = db.submission_get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    # Only the submission owner or admin can trigger matching
    if user["role"] != "admin" and submission["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="只能为自己的提交触发匹配")

    scenario = db.scenario_get_by_id(submission["scenario_id"])
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    match_config = scenario["match_config"]

    # If no embedding yet, generate and store it
    if not submission["embedding_vector"]:
        from app.services.matching import embed_and_store_submission
        embed_and_store_submission(
            submission_id,
            submission["form_data"],
            match_config.get("embedding_fields", []),
            submission["scenario_id"],
        )
        submission = db.submission_get_by_id(submission_id)

    try:
        matches = await run_matching(
            submission_id=submission_id,
            embedding_fields=match_config.get("embedding_fields", []),
            filter_fields=match_config.get("filter_fields", []),
            weight_fields=match_config.get("weight_fields", {}),
            top_k=match_config.get("top_k", 10),
            min_similarity=match_config.get("min_similarity", 0.0),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

    # Apply privacy filter
    matches = _apply_privacy(matches, user["role"], submission_id)

    return MatchResponse(
        submission_id=submission_id,
        matches=[MatchResultItem(**m) for m in matches],
    )


@router.get("/results/{submission_id}", response_model=MatchResponse)
def get_match_results(
    submission_id: str,
    user: dict = Depends(require_auth),
):
    """Get previously computed match results for a submission (auth required, ownership checked, privacy filtered)."""
    submission = db.submission_get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    # Allow: admin, submission owner, or scenario creator
    scenario = db.scenario_get_by_id(submission.get("scenario_id", ""))
    is_creator = scenario and scenario.get("creator_id") == user["id"]
    if user["role"] != "admin" and submission["user_id"] != user["id"] and not is_creator:
        raise HTTPException(status_code=403, detail="只能查看自己提交的匹配结果")

    match_rows = db.match_result_get_by_submission(submission_id)
    matches = []
    for row in match_rows:
        matched_sub = db.submission_get_by_id(row["matched_submission_id"])
        matches.append(MatchResultItem(
            submission_id=submission_id,
            matched_submission_id=row["matched_submission_id"],
            similarity_score=row["similarity_score"],
            matched_user_name=matched_sub["form_data"].get("name", "匿名用户") if matched_sub else "未知用户",
            matched_form_data=matched_sub["form_data"] if matched_sub else {},
            explanation=row.get("explanation", ""),
        ).model_dump())

    # Apply privacy filter
    matches = _apply_privacy(matches, user["role"], submission_id)

    return MatchResponse(
        submission_id=submission_id,
        matches=[MatchResultItem(**m) for m in matches],
    )


@router.get("/stats/scenario/{scenario_id}")
def get_scenario_matching_stats(
    scenario_id: str,
    user: dict = Depends(require_auth),
):
    """Get matching statistics for a scenario (auth required)."""
    scenario = db.scenario_get_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    submissions = db.submission_get_by_scenario(scenario_id)
    total_matches = 0
    matched_users = set()
    for sub in submissions:
        results = db.match_result_get_by_submission(sub["id"])
        if results:
            total_matches += len(results)
            matched_users.add(sub["id"])

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario["name"],
        "total_submissions": len(submissions),
        "total_matches": total_matches,
        "users_with_matches": len(matched_users),
        "avg_matches_per_user": total_matches / len(matched_users) if matched_users else 0,
    }
