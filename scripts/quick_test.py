import httpx, time

B = "http://localhost:8000/api"
c = httpx.Client(timeout=600)

# Create + publish
sc = c.post(f"{B}/scenarios", json={
    "name": "Milvus Test",
    "form_schema": {
        "fields": [
            {"key": "name", "type": "text", "label": "n", "required": True},
            {"key": "about", "type": "textarea", "label": "a", "required": True},
        ]
    },
    "match_config": {
        "embedding_fields": ["about"],
        "filter_fields": [],
        "weight_fields": {},
        "top_k": 3,
        "min_similarity": 0.0,
    },
    "ui_config": {"theme_color": "#667eea", "card_layout": "grid", "result_display": ["name"]},
    "status": "active",
})
sid = sc.json()["id"]
print(f"Scenario: {sid}")

# Submit 3 people
ids = []
for name, about in [
    ("Alice", "Outdoor hiking camping nature photography"),
    ("Bob", "Hiking enthusiast loves camping outdoors"),
    ("Charlie", "Indoor gaming anime computer"),
]:
    r = c.post(f"{B}/submissions", json={"scenario_id": sid, "form_data": {"name": name, "about": about}})
    sub_id = r.json()["id"]
    ids.append((name, sub_id))
    print(f"  {name}: {sub_id[:8]}")

print("Waiting for embeddings...")
time.sleep(5)

# Match Alice
print("Matching Alice...")
r = c.post(f"{B}/matching/run/{ids[0][1]}")
print(f"Match status: {r.status_code}")
data = r.json()
for m in data.get("matches", []):
    print(f"  {m['matched_user_name']}: {m['similarity_score']:.4f}")

# Check Milvus count
health = c.get(f"{B}/health").json()
print(f"\nMilvus vectors: {health['vectors_in_store']}")
print("DONE")
