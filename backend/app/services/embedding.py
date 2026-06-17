"""智谱（ZhipuAI）embedding 服务 — 使用 embedding-2 模型生成向量。"""

from zhipuai import ZhipuAI
from tenacity import retry, stop_after_attempt, wait_random_exponential
from app.config import ZHIPUAI_API_KEY, ZHIPUAI_EMBEDDING_MODEL

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)


@retry(wait=wait_random_exponential(min=5, max=60), stop=stop_after_attempt(5))
def _embedding_with_backoff(text: str) -> list[float]:
    """Call ZhipuAI embeddings API with exponential backoff retry.

    智谱原生 SDK 调用：
        client.embeddings.create(model="embedding-2", input=text)
        → response.data[0].embedding
    """
    response = client.embeddings.create(
        model=ZHIPUAI_EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector from text.

    Args:
        text: The text to embed.

    Returns:
        An embedding vector (1024 dimensions for embedding-2).
    """
    return _embedding_with_backoff(text)


def generate_embedding_from_fields(
    form_data: dict, embedding_fields: list[str]
) -> list[float]:
    """Generate an embedding from specified fields of form data.

    Combines the values of specified fields into a single text string,
    then generates an embedding.

    Args:
        form_data: The full form data dict.
        embedding_fields: List of field keys to include in the embedding.

    Returns:
        An embedding vector.
    """
    texts = []
    for field in embedding_fields:
        if field in form_data and form_data[field]:
            val = form_data[field]
            if isinstance(val, list):
                texts.append(" ".join(str(v) for v in val))
            else:
                texts.append(str(val))

    combined = " ".join(texts)
    if not combined.strip():
        # Fallback: use all text fields
        combined = " ".join(
            str(v) for v in form_data.values()
            if v is not None and not isinstance(v, (list, dict))
        )

    return _embedding_with_backoff(combined)
