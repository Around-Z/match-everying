"""FastAPI application entry point."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scenarios, submissions, matching, auth, admin
from app.database.mysql import init_db, get_db, _row_to_submission
from app.services.vector_svc import init_index, load_vectors, get_vector_count

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="多场景智能匹配平台",
    description="基于 Milvus 向量数据库的多场景智能匹配系统 — API",
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(scenarios.router)
app.include_router(submissions.router)
app.include_router(matching.router)


@app.on_event("startup")
async def startup():
    """Initialize database and Milvus vector store."""
    init_db()
    init_index()

    # If Milvus starts empty, migrate vectors from SQLite (cold start / recovery)
    vcount = get_vector_count()
    if vcount == 0:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM submissions WHERE embedding_vector IS NOT NULL"
        ).fetchall()
        conn.close()
        vectors = [_row_to_submission(r) for r in rows]
        if vectors:
            load_vectors(vectors)

    print(f"Milvus ready: {get_vector_count()} vectors in collection.")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "service": "matching-platform",
        "vectors_in_store": get_vector_count(),
    }
