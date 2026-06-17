"""Matching engine — orchestrates embedding + vector search + result ranking."""

from typing import Optional
from app.services.embedding import generate_embedding_from_fields
from app.services.vector_svc import upsert_vector, query_similar
from app.services.llm import explain_match
from app.database.mysql import (
    submission_get_by_id,
    submission_get_all_with_embeddings,
    match_result_save,
    match_result_get_by_submission,
)


async def run_matching(
    submission_id: str,
    embedding_fields: list[str],
    filter_fields: list[str],
    weight_fields: dict[str, float],
    top_k: int = 10,
    min_similarity: float = 0.7,
) -> list[dict]:
    """Run the full matching pipeline for a submission.

    1. Get the submission's embedding
    2. Query local vector store for similar vectors
    3. Build structured filter from filter_fields
    4. Apply weight adjustments
    5. Save match results
    6. Generate explanations (async)

    Args:
        submission_id: The submission to match.
        embedding_fields: Fields used for embedding.
        filter_fields: Fields for exact filtering.
        weight_fields: Fields to weight into score.
        top_k: Number of matches to return.
        min_similarity: Minimum similarity threshold.

    Returns:
        List of match result dicts with explanations.
    """
    submission = submission_get_by_id(submission_id)
    if not submission or not submission["embedding_vector"]:
        raise ValueError(f"Submission {submission_id} not found or has no embedding")

    # Build filter: always restrict to same scenario + add filter_fields
    local_filter = {"_scenario_id": submission["scenario_id"]}
    for field in filter_fields:
        if field in submission["form_data"] and submission["form_data"][field] is not None:
            local_filter[field] = submission["form_data"][field]

    # Query local vector store
    raw_matches = query_similar(
        vector=submission["embedding_vector"],
        top_k=top_k + 1,  # +1 to account for self-match
        filter_dict=local_filter if local_filter else None,
        exclude_ids=[submission_id],
    )

    # Filter and rank
    matches = []
    for m in raw_matches:
        if m["score"] < min_similarity:
            continue

        matched_sub = submission_get_by_id(m["id"])
        if not matched_sub:
            continue

        # Calculate weighted score
        score = m["score"]
        for field, weight in weight_fields.items():
            if field in m["metadata"] and m["metadata"][field] is not None:
                try:
                    normalized = float(m["metadata"][field]) / 100.0
                    score = score * (1 - weight) + normalized * weight
                except (ValueError, TypeError):
                    pass

        # Generate match explanation
        explanation = ""
        try:
            explanation = await explain_match(
                submission["form_data"], matched_sub["form_data"]
            )
        except Exception:
            explanation = "匹配解释生成失败，请稍后重试。"

        # Save match result
        match_result_save(submission_id, m["id"], score, explanation)

        matches.append({
            "submission_id": submission_id,
            "matched_submission_id": m["id"],
            "similarity_score": round(score, 4),
            "matched_user_name": matched_sub["form_data"].get("name", "匿名用户"),
            "matched_form_data": matched_sub["form_data"],
            "explanation": explanation,
        })

    # Sort by score descending
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    return matches[:top_k]


def embed_and_store_submission(
    submission_id: str,
    form_data: dict,
    embedding_fields: list[str],
    scenario_id: str = "",
    filter_metadata: dict | None = None,
):
    """Generate embedding for a submission and store it locally.

    User tags (_user_tags in form_data) are automatically appended to the
    embedding text so they influence matching across all scenarios.
    """
    # Build embedding text from specified fields + user tags
    texts = []
    for field in embedding_fields:
        if field in form_data and form_data[field]:
            val = form_data[field]
            if isinstance(val, list):
                texts.append(" ".join(str(v) for v in val))
            else:
                texts.append(str(val))

    # Auto-inject user tags into embedding text
    user_tags = form_data.get("_user_tags", [])
    if user_tags:
        texts.append("用户标签: " + ", ".join(user_tags))

    combined = " ".join(texts)
    if not combined.strip():
        combined = " ".join(
            str(v) for v in form_data.values()
            if v is not None and not isinstance(v, (list, dict))
        )

    from app.services.embedding import _embedding_with_backoff
    vector = _embedding_with_backoff(combined)

    # Build metadata from form_data for filtering
    metadata = {"_scenario_id": scenario_id}
    for key, value in form_data.items():
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
        elif isinstance(value, list):
            metadata[key] = ", ".join(str(v) for v in value)
    if filter_metadata:
        metadata.update(filter_metadata)

    upsert_vector(submission_id, vector, metadata)

    from app.database.mysql import submission_update_embedding
    submission_update_embedding(submission_id, vector)
