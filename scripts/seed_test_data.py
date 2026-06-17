"""
Seed test data for matching accuracy validation.

Design: 4 interest groups × 4 people each = 16 people total.
- Group A: outdoor/nature lovers
- Group B: gaming/anime fans
- Group C: food/cooking enthusiasts
- Group D: sports/fitness lovers

Expected: intra-group similarity > 0.6, inter-group similarity < 0.5
"""
import httpx
import json
import time
import sys

BASE = "http://localhost:8000/api"
CLIENT = httpx.Client(timeout=300)

from tenacity import retry, stop_after_attempt, wait_exponential

# ── Test Data ──────────────────────────────────────────────
TEST_PEOPLE = {
    "outdoor": [
        {"name": "大山",  "about": "热爱户外徒步和登山，每周都去郊野公园露营，喜欢拍摄自然风光，希望找到一起探索大自然的伙伴"},
        {"name": "小溪",  "about": "资深户外爱好者，徒步过很多名山大川，擅长野外生存技能，喜欢篝火露营看星星，想找同样热爱户外的搭子"},
        {"name": "林风",  "about": "喜欢背包旅行和野外探险，对摄影很感兴趣，周末常去爬山拍日出，期待遇到热爱户外的朋友"},
        {"name": "云野",  "about": "大自然的狂热粉丝，热衷于登山、露营、皮划艇等户外运动，享受远离城市喧嚣的感觉"},
    ],
    "gaming": [
        {"name": "电竞小子","about": "王者荣耀钻石段位，喜欢打野和对抗路，也玩原神和崩坏，二次元爱好者，宅家打游戏是最爱"},
        {"name": "宅宅乐",  "about": "游戏宅一枚，steam库里几百个游戏，最爱RPG和策略类，也追番看动漫，想找游戏搭子开黑"},
        {"name": "次元壁",  "about": "重度二次元+游戏玩家，原神60级老玩家，LOL钻石，周末就是打游戏追番，偶尔去漫展"},
        {"name": "游侠",    "about": "玩游戏十多年了，各种类型都玩，最近沉迷崩坏星穹铁道，也在打王者荣耀，宅家打游戏最舒服"},
    ],
    "cooking": [
        {"name": "美食家","about": "热爱烹饪和烘焙，喜欢研究各国料理，周末喜欢去菜市场挑选新鲜食材，做出美味的家常菜"},
        {"name": "甜品控","about": "烘焙爱好者，擅长做蛋糕和面包，也喜欢探店各种甜品店，想找一起研究美食的伙伴"},
        {"name": "厨房达人","about": "对烹饪充满热情，拿手菜红烧肉和麻婆豆腐，也喜欢尝试新菜谱，探索不同地方的美食文化"},
        {"name": "味蕾探险家","about": "美食探店达人，热爱发掘隐藏的街头小吃和特色餐厅，也喜欢自己动手复刻经典菜肴"},
    ],
    "sports": [
        {"name": "运动达人","about": "每天坚持健身房锻炼，喜欢力量训练和有氧运动，也打篮球和游泳，追求健康生活方式"},
        {"name": "跑步者",  "about": "马拉松爱好者，每周跑量50公里以上，参加过多个城市马拉松，也喜欢越野跑和铁人三项"},
        {"name": "健身狂",  "about": "健身房的常客，热爱撸铁和塑形训练，对营养学也有研究，想找一起健身互相监督的伙伴"},
        {"name": "球场飞人","about": "篮球狂热爱好者，每周至少打3场球，也喜欢羽毛球和乒乓球，运动是我生活中最重要的事"},
    ],
}


def create_scenario():
    """Create the matching scenario."""
    resp = CLIENT.post(f"{BASE}/scenarios", json={
        "name": "兴趣匹配验证测试",
        "description": "用于验证向量匹配准确度的测试场景",
        "form_schema": {
            "fields": [
                {"key": "name", "type": "text", "label": "昵称", "required": True},
                {"key": "about", "type": "textarea", "label": "自我介绍", "required": True,
                 "placeholder": "描述你的兴趣爱好、生活方式、对匹配的期望"},
            ]
        },
        "match_config": {
            "embedding_fields": ["about"],
            "filter_fields": [],
            "weight_fields": {},
            "top_k": 5,
            "min_similarity": 0.0,
        },
        "ui_config": {"theme_color": "#667eea", "card_layout": "grid", "result_display": ["name"]},
        "status": "active",
    })
    sid = resp.json()["id"]
    print(f"Scenario created: {sid}")
    return sid


def submit_all(scenario_id):
    """Submit all test people."""
    ids = {}  # group_name → [submission_ids]
    for group, people in TEST_PEOPLE.items():
        ids[group] = []
        for person in people:
            resp = CLIENT.post(f"{BASE}/submissions", json={
                "scenario_id": scenario_id,
                "form_data": person,
            })
            sid = resp.json()["id"]
            ids[group].append(sid)
            print(f"  [{group}] {person['name']} → {sid[:8]}")
    return ids


def run_matching(submission_ids, wait=8):
    """Run matching for all submissions and collect results."""
    print(f"\nWaiting {wait}s for embeddings...")
    time.sleep(wait)

    all_results = {}
    total = sum(len(ids) for ids in submission_ids.values())
    done = 0
    for group, id_list in submission_ids.items():
        for sid in id_list:
            # Retry on timeout
            for attempt in range(3):
                try:
                    resp = CLIENT.post(f"{BASE}/matching/run/{sid}")
                    data = resp.json()
                    all_results[sid] = data.get("matches", [])
                    done += 1
                    print(f"  [{done}/{total}] {sid[:8]} → {len(all_results[sid])} matches")
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"    Retry {attempt+1}: {e}")
                        time.sleep(3)
                    else:
                        print(f"    FAILED: {e}")
                        all_results[sid] = []
    return all_results


def evaluate(ids_by_group, match_results):
    """Evaluate matching accuracy."""
    # Build lookup: submission_id → group
    id_to_group = {}
    id_to_name = {}
    for group, id_list in ids_by_group.items():
        for sid in id_list:
            id_to_group[sid] = group
            # Find name
            for p in TEST_PEOPLE[group]:
                if id_to_name.get(sid) is None:
                    id_to_name[sid] = p["name"]

    print("\n" + "=" * 70)
    print("  MATCHING ACCURACY REPORT")
    print("=" * 70)

    # Per-group intra/inter analysis
    total_intra_scores = []
    total_inter_scores = []
    group_stats = {}

    for group in TEST_PEOPLE:
        intra = []
        inter = []
        for sid in ids_by_group[group]:
            matches = match_results.get(sid, [])
            for m in matches:
                matched_id = m["matched_submission_id"]
                if matched_id in id_to_group:
                    if id_to_group[matched_id] == group:
                        intra.append(m["similarity_score"])
                    else:
                        inter.append(m["similarity_score"])

        avg_intra = sum(intra) / len(intra) if intra else 0
        avg_inter = sum(inter) / len(inter) if inter else 0
        group_stats[group] = {"intra": intra, "inter": inter, "avg_intra": avg_intra, "avg_inter": avg_inter}
        total_intra_scores.extend(intra)
        total_inter_scores.extend(inter)
        print(f"\n[{group}] 组内:{len(intra)}对 avg={avg_intra:.4f} | 组间:{len(inter)}对 avg={avg_inter:.4f}")

    avg_all_intra = sum(total_intra_scores) / len(total_intra_scores) if total_intra_scores else 0
    avg_all_inter = sum(total_inter_scores) / len(total_inter_scores) if total_inter_scores else 0

    print(f"\n{'─' * 50}")
    print(f"  总体: 组内 avg={avg_all_intra:.4f}  |  组间 avg={avg_all_inter:.4f}")
    print(f"  区分度: {avg_all_intra - avg_all_inter:.4f} (越大越好，>0.15 即良好)")
    print(f"{'─' * 50}")

    # Show top matches for each person
    print("\n── 每人 Top3 匹配 ──")
    for group in TEST_PEOPLE:
        for sid in ids_by_group[group]:
            name = id_to_name[sid]
            matches = match_results.get(sid, [])[:3]
            print(f"\n  {name} ({group}):")
            for i, m in enumerate(matches):
                matched_group = id_to_group.get(m["matched_submission_id"], "?")
                tag = "[SAME]" if matched_group == group else "[DIFF]"
                print(f"    #{i+1} {m['matched_user_name']} [{matched_group}] score={m['similarity_score']:.4f} {tag}")

    # Accuracy: top-3 hits (how many top-3 matches are from same group)
    hits = 0
    total = 0
    for group in TEST_PEOPLE:
        for sid in ids_by_group[group]:
            matches = match_results.get(sid, [])[:3]
            for m in matches:
                total += 1
                if id_to_group.get(m["matched_submission_id"]) == group:
                    hits += 1
    precision = hits / total * 100 if total else 0
    print(f"\n═══ Top-3 Precision: {hits}/{total} = {precision:.1f}% ═══")
    print(f"    (same-group matches in top-3)")

    return {
        "avg_intra": avg_all_intra,
        "avg_inter": avg_all_inter,
        "discrimination": avg_all_intra - avg_all_inter,
        "top3_precision": precision,
    }


def main():
    print("=" * 50)
    print("  Seed Test Data for Matching Validation")
    print("=" * 50)

    # 1. Create scenario
    sid = create_scenario()

    # 2. Submit all test people
    print("\nSubmitting test data...")
    ids = submit_all(sid)

    # 3. Run matching
    print("\nRunning matching...")
    results = run_matching(ids)

    # 4. Evaluate
    stats = evaluate(ids, results)

    # 5. Export for inspection
    export = {
        "scenario_id": sid,
        "groups": {g: [p["name"] for p in people] for g, people in TEST_PEOPLE.items()},
        "stats": stats,
    }
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    print(f"\nResults exported to test_results.json")

    return 0 if stats["top3_precision"] >= 60 else 1


if __name__ == "__main__":
    sys.exit(main())
