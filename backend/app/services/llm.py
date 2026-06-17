"""DeepSeek API service for UI schema generation and match explanations."""

import json
import httpx
from tenacity import retry, stop_after_attempt, wait_random_exponential
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_CHAT_MODEL


SYSTEM_PROMPT_GENERATE_SCENARIO = """You are an AI that helps create matching platform scenarios.
Given a user's natural language description, you generate a structured matching scenario configuration.

Output format (JSON only, no other text):
{
  "name": "Short name for the scenario",
  "description": "Brief description in Chinese",
  "form_schema": {
    "fields": [
      {
        "key": "field_key",
        "type": "text|textarea|number|select|multi_select|slider|date|tag_input|contact",
        "label": "Display label in Chinese",
        "required": true/false,
        "placeholder": "placeholder text (optional)",
        "options": ["option1", "option2"],  // for select/multi_select only
        "min": 0,   // for number/slider only
        "max": 100, // for number/slider only
        "step": 1   // for number/slider only
      }
    ]
  },
  "match_config": {
    "embedding_source": "composite",
    "embedding_fields": ["field_keys_to_embed"],
    "filter_fields": ["field_keys_for_exact_filter"],
    "weight_fields": {"field_key": weight},
    "top_k": 10,
    "min_similarity": 0.7
  },
  "ui_config": {
    "theme_color": "#hexcolor",
    "card_layout": "grid|list|swipe",
    "result_display": ["field_keys_to_show_in_results"]
  }
}

Rules:
1. form_schema.fields: Define ALL fields the participant needs to fill. Choose appropriate types.
2. **CRITICAL**: Every scenario MUST include a contact field: {"key":"contact","type":"contact","label":"联系方式","required":true,"placeholder":"微信号/手机号/QQ号"}
3. match_config.embedding_fields: Fields with free text that capture personality/preferences. DO NOT include the contact field here.
4. match_config.filter_fields: Fields that need exact or range matching (gender, rank tier, etc.)
5. match_config.weight_fields: Numeric fields to weight into the final score.
6. ui_config: Choose appropriate theme and layout.
7. ALL labels and descriptions must be in Chinese."""


SYSTEM_PROMPT_EXPLAIN_MATCH = """你是一个匹配解释助手。根据两个人的资料，解释为什么他们匹配。

请用中文回复，给出 3-5 条理由，以要点列表格式输出。
每条理由应当具体、个性化，引用他们资料中的共同点或互补之处。
每条以 "- " 开头。"""


@retry(wait=wait_random_exponential(min=5, max=60), stop=stop_after_attempt(3))
async def _deepseek_chat(messages: list[dict], temperature: float = 0.3) -> str:
    """Call DeepSeek chat API with retry."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_CHAT_MODEL,
                "messages": messages,
                "temperature": temperature,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def generate_scenario_config(user_prompt: str) -> dict:
    """Generate a scenario configuration from natural language description.

    Args:
        user_prompt: User's description of the matching scenario.

    Returns:
        Parsed JSON dict with name, description, form_schema, match_config, ui_config.
    """
    content = await _deepseek_chat([
        {"role": "system", "content": SYSTEM_PROMPT_GENERATE_SCENARIO},
        {"role": "user", "content": user_prompt},
    ])

    # Extract JSON from response (may be wrapped in markdown code block)
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])
    if content.startswith("json"):
        content = content[4:]

    return json.loads(content)


async def explain_match(person_a_data: dict, person_b_data: dict) -> str:
    """Generate a match explanation for two people.

    Args:
        person_a_data: Form data of person A.
        person_b_data: Form data of person B.

    Returns:
        Chinese text with bullet-point reasons.
    """
    prompt = (
        f"以下两个人的资料，请解释他们为什么匹配：\n\n"
        f"人A的资料：{json.dumps(person_a_data, ensure_ascii=False)}\n\n"
        f"人B的资料：{json.dumps(person_b_data, ensure_ascii=False)}\n\n"
        f"他们已经在向量匹配中被判定为高度相似。请结合上述信息具体解释他们为什么是好的匹配。"
    )

    content = await _deepseek_chat([
        {"role": "system", "content": SYSTEM_PROMPT_EXPLAIN_MATCH},
        {"role": "user", "content": prompt},
    ])

    return content.strip()
