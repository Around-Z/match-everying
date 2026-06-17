"""Authentication API routes — register, login, profile."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.models.scenario import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    UserUpdate,
)
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_auth,
)
from app.database import mysql as db
from app.database.mysql import (
    user_create,
    user_get_by_email,
    user_get_by_id,
    submission_get_by_user,
    match_result_get_by_user,
)

logger = logging.getLogger("auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: UserRegister):
    """Register a new user account. Returns JWT tokens."""
    # Validate role
    if data.role not in ("participant", "designer"):
        raise HTTPException(status_code=400, detail="Role must be participant or designer")

    # Check duplicate email
    if user_get_by_email(data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    pw_hash = hash_password(data.password)
    uid = user_create(data.email, data.username, pw_hash, data.role,
                      contact_info=data.contact_info)

    # Issue tokens
    user = user_get_by_id(uid)
    access_token = create_access_token({"sub": uid})
    refresh_token = create_refresh_token({"sub": uid})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(**user),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, request: Request):
    """Login with email and password. Returns JWT tokens."""
    client_ip = request.client.host if request.client else "unknown"
    user = user_get_by_email(data.email)
    if not user:
        logger.warning(f"Login failed — unknown email '{data.email}' from {client_ip}")
        raise HTTPException(status_code=401, detail="邮箱未注册，请先创建账户")
    if not verify_password(data.password, user["password_hash"]):
        logger.warning(f"Login failed — wrong password for '{data.email}' from {client_ip}")
        raise HTTPException(status_code=401, detail="密码错误，请重试")

    logger.info(f"Login success — user='{user['username']}' role='{user['role']}' from {client_ip}")
    access_token = create_access_token({"sub": user["id"]})
    refresh_token = create_refresh_token({"sub": user["id"]})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(**user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token_str: str):
    """Exchange a refresh token for a new access token pair."""
    try:
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = user_get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token({"sub": user["id"]})
    new_refresh = create_refresh_token({"sub": user["id"]})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        user=UserResponse(**user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(user: dict = Depends(require_auth)):
    """Get the current logged-in user's profile."""
    return UserResponse(**user)


@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, user: dict = Depends(require_auth)):
    """Update current user's profile."""
    from app.database.mysql import user_update_profile, user_get_by_id
    update_data = data.model_dump(exclude_none=True)
    if update_data:
        user_update_profile(user["id"], update_data)
    updated_user = user_get_by_id(user["id"])
    return UserResponse(**updated_user)


@router.get("/me/submissions")
def get_my_submissions(user: dict = Depends(require_auth)):
    """Get all submissions made by the current user, enriched with scenario info."""
    subs = submission_get_by_user(user["id"])
    enriched = []
    for s in subs:
        scenario = db.scenario_get_by_id(s["scenario_id"])
        s["scenario_name"] = scenario["name"] if scenario else "已删除的场景"
        s["scenario_status"] = scenario["status"] if scenario else "unknown"
        enriched.append(s)
    return {"submissions": enriched, "total": len(enriched)}


@router.get("/me/matches")
def get_my_matches(user: dict = Depends(require_auth)):
    """Get all match results for the current user's submissions, enriched with scenario info."""
    matches = match_result_get_by_user(user["id"])
    enriched = []
    for m in matches:
        # Find which scenario this match belongs to
        sub = db.submission_get_by_id(m.get("submission_id", ""))
        if sub:
            scenario = db.scenario_get_by_id(sub["scenario_id"])
            m["scenario_id"] = sub["scenario_id"]
            m["scenario_name"] = scenario["name"] if scenario else "已删除的场景"
        else:
            m["scenario_id"] = ""
            m["scenario_name"] = "未知场景"
        enriched.append(m)
    return {"matches": enriched, "total": len(enriched)}
