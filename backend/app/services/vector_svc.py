"""Milvus 向量服务 — Docker Milvus Standalone。

- embedding 向量 → Milvus（持久化，ANN 索引，标量过滤）
- 业务数据 → SQLite
- 通过 submission_id 关联
"""

from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema
from pymilvus.milvus_client.index import IndexParams
from app.config import (
    MILVUS_HOST,
    MILVUS_PORT,
    MILVUS_COLLECTION,
    EMBEDDING_DIMENSION,
)

_client: MilvusClient | None = None


def get_client() -> MilvusClient:
    global _client
    if _client is None:
        _client = MilvusClient(uri=f"http://{MILVUS_HOST}:{MILVUS_PORT}")
    return _client


def _ensure_index(client: MilvusClient):
    """Ensure IVF_FLAT index exists on the vector field."""
    idx = IndexParams()
    idx.add_index(field_name="vector", index_type="IVF_FLAT", metric_type="COSINE", nlist=128)
    client.create_index(collection_name=MILVUS_COLLECTION, index_params=idx)
    print(f"Index created on '{MILVUS_COLLECTION}'.")


def init_index():
    """初始化 Milvus 集合与索引，确保 VARCHAR 主键 + 动态字段可用。"""
    client = get_client()

    if not client.has_collection(MILVUS_COLLECTION):
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIMENSION),
        ]
        schema = CollectionSchema(fields=fields, enable_dynamic_field=True)
        client.create_collection(collection_name=MILVUS_COLLECTION, schema=schema)
        print(f"Milvus collection '{MILVUS_COLLECTION}' created.")
        _ensure_index(client)
    else:
        print(f"Milvus collection '{MILVUS_COLLECTION}' already exists.")

    # load_collection requires an index — create one if missing (e.g. leftover collection from failed init)
    try:
        client.load_collection(MILVUS_COLLECTION)
    except Exception as e:
        if "index not found" in str(e).lower():
            print("Index missing on existing collection — creating now...")
            _ensure_index(client)
            client.load_collection(MILVUS_COLLECTION)
        else:
            raise


def load_vectors(vectors: list[dict]):
    """从 SQLite 批量导入向量到 Milvus。"""
    client = get_client()
    records = []
    for v in vectors:
        vec = v.get("embedding_vector")
        if not vec:
            continue
        form_data = v.get("form_data", {}) or {}
        record = {"id": v["id"], "vector": vec, "scenario_id": v.get("scenario_id", "")}
        for key, val in form_data.items():
            if isinstance(val, (str, int, float, bool)):
                record[key] = val
            elif isinstance(val, list):
                record[key] = ", ".join(str(x) for x in val)
        records.append(record)
    if records:
        result = client.insert(collection_name=MILVUS_COLLECTION, data=records)
        client.flush(MILVUS_COLLECTION)
        print(f"Loaded {result['insert_count']} vectors from SQLite into Milvus.")


def upsert_vector(
    vector_id: str,
    vector: list[float],
    metadata: dict | None = None,
):
    """存储/更新向量到 Milvus。"""
    client = get_client()
    record = {"id": vector_id, "vector": vector}
    if metadata:
        record.update(metadata)
    client.upsert(collection_name=MILVUS_COLLECTION, data=[record])
    client.flush(MILVUS_COLLECTION)


def _filter_to_expr(d: dict) -> str:
    parts = []
    for k, v in d.items():
        if isinstance(v, str):
            parts.append(f'{k} == "{v}"')
        elif isinstance(v, (int, float)):
            parts.append(f"{k} == {v}")
        elif isinstance(v, bool):
            parts.append(f"{k} == {str(v).lower()}")
    return " && ".join(parts) if parts else ""


def query_similar(
    vector: list[float],
    top_k: int = 10,
    filter_dict: dict | None = None,
    exclude_ids: list[str] | None = None,
) -> list[dict]:
    """查询相似向量（COSINE）。"""
    client = get_client()
    filters = []
    if filter_dict:
        f = _filter_to_expr(filter_dict)
        if f:
            filters.append(f)
    if exclude_ids:
        ids_str = ", ".join(f'"{x}"' for x in exclude_ids)
        filters.append(f"id not in [{ids_str}]")

    results = client.search(
        collection_name=MILVUS_COLLECTION,
        data=[vector],
        limit=top_k,
        filter=" && ".join(filters) if filters else "",
        output_fields=["*"],
    )
    if not results or not results[0]:
        return []

    matches = []
    for hit in results[0]:
        entity = hit.get("entity", {})
        matches.append({
            "id": entity.get("id", ""),
            "score": round(hit.get("distance", 0), 6),
            "metadata": {k: v for k, v in entity.items() if k not in ("id", "vector")},
        })
    return matches


def delete_vector(vector_id: str):
    get_client().delete(collection_name=MILVUS_COLLECTION, filter=f'id == "{vector_id}"')


def get_vector_count() -> int:
    try:
        return get_client().get_collection_stats(MILVUS_COLLECTION).get("row_count", 0)
    except Exception:
        return 0
