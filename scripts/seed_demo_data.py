"""
Demo data seeder — creates diverse users, scenarios, submissions, and match results.
All via HTTP API. Backend must be running on port 8001.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
import time
import json

API = "http://localhost:8001/api"
HEADERS = {"Content-Type": "application/json"}

def api(method, path, **kw):
    """Call API and return JSON, or print error and exit."""
    try:
        r = requests.request(method, f"{API}{path}", headers=HEADERS, timeout=30, **kw)
        if r.status_code == 204:
            return {}
        data = r.json()
        if r.status_code >= 400:
            print(f"  [ERR] {method} {path} -> {r.status_code}: {data.get('detail', data)}")
            return None
        return data
    except Exception as e:
        print(f"  [ERR] {method} {path} -> {e}")
        return None

def register(email, username, password, contact_info, role="participant"):
    """Register a user, return dict with token + user."""
    data = api("POST", "/auth/register", json={
        "email": email, "username": username, "password": password,
        "contact_info": contact_info, "role": role,
    })
    return data

def login(email, password):
    return api("POST", "/auth/login", json={"email": email, "password": password})

def update_tags(token, tags):
    return requests.put(f"{API}/auth/me", headers={**HEADERS, "Authorization": f"Bearer {token}"},
                        json={"tags": tags}).json()

def create_scenario(token, scenario_data):
    return requests.post(f"{API}/scenarios", headers={**HEADERS, "Authorization": f"Bearer {token}"},
                         json=scenario_data).json()

def submit(token, scenario_id, form_data):
    return requests.post(f"{API}/submissions", headers={**HEADERS, "Authorization": f"Bearer {token}"},
                         json={"scenario_id": scenario_id, "form_data": form_data}).json()

def run_matching(token, submission_id):
    return requests.post(f"{API}/matching/run/{submission_id}",
                         headers={**HEADERS, "Authorization": f"Bearer {token}"}).json()

# ============================================================
print("=" * 60)
print("  Demo Data Seeder")
print("=" * 60)

# === PHASE 1: Users ===
print("\n[1/5] Creating users...")

users = {}
for name, email, role in [
    ("小明", "xm@demo.com", "participant"),
    ("小红", "xh@demo.com", "participant"),
    ("大壮", "dz@demo.com", "participant"),
    ("学霸张", "xbz@demo.com", "participant"),
    ("学渣李", "xzl@demo.com", "participant"),
    ("健身王", "jsw@demo.com", "participant"),
    ("设计师A", "dsn@demo.com", "designer"),
]:
    r = register(email, name, "demo123456", f"wx_{name}", role)
    if r:
        users[name] = {"token": r["access_token"], "user": r["user"]}
        print(f"  [OK] {name} ({role})")
    else:
        # Try login (maybe already exists)
        r = login(email, "demo123456")
        if r:
            users[name] = {"token": r["access_token"], "user": r["user"]}
            print(f"  [OK] {name} (existing, logged in)")

# Admin
r = login("admin@qm.com", "admin123")
if r:
    users["管理员"] = {"token": r["access_token"], "user": r["user"]}
    print(f"  [OK] 管理员 (admin)")

# === PHASE 2: Scenarios ===
print("\n[2/5] Creating scenarios...")

dsn_token = users["设计师A"]["token"]

# Scenario 1: 王者荣耀
wzry = {
    "name": "王者荣耀队友匹配",
    "description": "找到与你段位、分路和风格完美契合的王者荣耀队友。一起冲王者！",
    "form_schema": {
        "fields": [
            {"key": "name", "type": "text", "label": "游戏昵称", "required": True},
            {"key": "rank", "type": "select", "label": "当前段位", "required": True,
             "options": ["青铜", "白银", "黄金", "铂金", "钻石", "星耀", "王者", "荣耀王者"]},
            {"key": "lane", "type": "select", "label": "擅长分路", "required": True,
             "options": ["打野", "中路", "发育路", "对抗路", "辅助"]},
            {"key": "winrate", "type": "number", "label": "胜率(%)", "min": 0, "max": 100, "required": True},
            {"key": "style", "type": "textarea", "label": "游戏风格与英雄池", "required": True,
             "placeholder": "描述你的游戏风格和擅长英雄..."},
            {"key": "contact", "type": "contact", "label": "联系方式", "required": True,
             "placeholder": "微信号/游戏ID"},
        ]
    },
    "match_config": {
        "embedding_source": "composite",
        "embedding_fields": ["style", "lane", "rank"],
        "filter_fields": [],
        "weight_fields": {"winrate": 0.2},
        "top_k": 5,
        "min_similarity": 0.5,
    },
    "ui_config": {
        "theme_color": "#e74c3c",
        "card_layout": "grid",
        "result_display": ["name", "rank", "lane", "winrate", "style"],
    },
    "status": "active",
}
r = create_scenario(dsn_token, wzry)
if r:
    wzry_id = r["id"]
    print(f"  [OK] 王者荣耀队友匹配 ({wzry_id})")
else:
    print(f"  [FAIL] 王者荣耀 failed")
    sys.exit(1)

# Scenario 2: 考研学习搭子
study = {
    "name": "考研学习搭子匹配",
    "description": "匹配与你目标一致、学习节奏同步的考研伙伴。互相监督，一起上岸！",
    "form_schema": {
        "fields": [
            {"key": "name", "type": "text", "label": "姓名", "required": True},
            {"key": "target_school", "type": "text", "label": "目标院校", "required": True},
            {"key": "major", "type": "text", "label": "报考专业", "required": True},
            {"key": "study_hours", "type": "slider", "label": "每天学习时长(小时)", "min": 0, "max": 14, "step": 1, "required": True},
            {"key": "weak_subjects", "type": "multi_select", "label": "弱势科目", "required": True,
             "options": ["英语", "数学", "政治", "专业课"]},
            {"key": "intro", "type": "textarea", "label": "自我介绍与学习目标", "required": True},
            {"key": "contact", "type": "contact", "label": "联系方式", "required": True},
        ]
    },
    "match_config": {
        "embedding_source": "composite",
        "embedding_fields": ["intro", "target_school", "major", "weak_subjects"],
        "filter_fields": [],
        "weight_fields": {"study_hours": 0.15},
        "top_k": 5,
        "min_similarity": 0.5,
    },
    "ui_config": {
        "theme_color": "#3498db",
        "card_layout": "list",
        "result_display": ["name", "target_school", "major", "study_hours", "weak_subjects"],
    },
    "status": "active",
}
r = create_scenario(dsn_token, study)
if r:
    study_id = r["id"]
    print(f"  [OK] 考研学习搭子匹配 ({study_id})")
else:
    sys.exit(1)

# Scenario 3: 健身
fitness = {
    "name": "健身伙伴匹配",
    "description": "找到训练目标和节奏一致的健身搭子。一起增肌减脂，互相激励！",
    "form_schema": {
        "fields": [
            {"key": "name", "type": "text", "label": "名字", "required": True},
            {"key": "goal", "type": "select", "label": "健身目标", "required": True,
             "options": ["增肌", "减脂", "塑形", "力量提升", "体能训练"]},
            {"key": "years", "type": "number", "label": "训练年限", "min": 0, "max": 20, "required": True},
            {"key": "days_per_week", "type": "number", "label": "每周训练天数", "min": 1, "max": 7, "required": True},
            {"key": "time_slot", "type": "select", "label": "偏好训练时间", "required": True,
             "options": ["清晨(6-8点)", "上午(9-11点)", "中午(12-14点)", "下午(15-17点)", "晚上(18-21点)"]},
            {"key": "intro", "type": "textarea", "label": "训练经历与目标", "required": True},
            {"key": "contact", "type": "contact", "label": "联系方式", "required": True},
        ]
    },
    "match_config": {
        "embedding_source": "composite",
        "embedding_fields": ["intro", "goal", "time_slot"],
        "filter_fields": [],
        "weight_fields": {"years": 0.1, "days_per_week": 0.15},
        "top_k": 5,
        "min_similarity": 0.5,
    },
    "ui_config": {
        "theme_color": "#27ae60",
        "card_layout": "grid",
        "result_display": ["name", "goal", "years", "days_per_week", "time_slot"],
    },
    "status": "active",
}
r = create_scenario(dsn_token, fitness)
if r:
    fitness_id = r["id"]
    print(f"  [OK] 健身伙伴匹配 ({fitness_id})")
else:
    sys.exit(1)

# Scenario 4: 摄影 (draft)
photo = {
    "name": "摄影约拍匹配",
    "description": "找到摄影风格契合的约拍伙伴。人像、风光、街拍... 一起捕捉美好瞬间。",
    "form_schema": {
        "fields": [
            {"key": "name", "type": "text", "label": "名字", "required": True},
            {"key": "style", "type": "select", "label": "摄影风格", "required": True,
             "options": ["人像摄影", "风光摄影", "街拍摄影", "静物摄影", "纪实摄影"]},
            {"key": "gear", "type": "text", "label": "常用器材", "required": True,
             "placeholder": "如：Sony A7M4 + 24-70 f/2.8"},
            {"key": "experience", "type": "number", "label": "摄影经验(年)", "min": 0, "max": 30, "required": True},
            {"key": "genres", "type": "multi_select", "label": "擅长题材", "required": True,
             "options": ["人像", "风光", "街拍", "静物", "夜景", "活动", "宠物", "美食"]},
            {"key": "contact", "type": "contact", "label": "联系方式", "required": True},
        ]
    },
    "match_config": {
        "embedding_source": "composite",
        "embedding_fields": ["style", "gear", "genres"],
        "filter_fields": [],
        "weight_fields": {"experience": 0.1},
        "top_k": 5,
        "min_similarity": 0.5,
    },
    "ui_config": {
        "theme_color": "#9b59b6",
        "card_layout": "grid",
        "result_display": ["name", "style", "gear", "experience", "genres"],
    },
    "status": "draft",
}
r = create_scenario(dsn_token, photo)
if r:
    photo_id = r["id"]
    print(f"  [OK] 摄影约拍匹配 ({photo_id}) (draft)")
else:
    sys.exit(1)

# === PHASE 3: Submissions ===
print("\n[3/5] Creating submissions...")

# -- 王者荣耀 submissions --
wzry_subs = [
    ("小明", {"name": "小明仔", "rank": "星耀", "lane": "打野", "winrate": 62, "style": "主玩韩信、澜、镜，擅长前期带节奏和抓人。打野节奏稳定，反野意识强。喜欢和会配合的中辅一起排位。最近在练裴擒虎。", "contact": "wx_xiaoming"}),
    ("小红", {"name": "小红花", "rank": "钻石", "lane": "辅助", "winrate": 55, "style": "主玩瑶、蔡文姬、孙膑。保护型辅助，跟射手走发育路。会看地图报点，团战站位好。想找实力强的打野或射手双排。", "contact": "wx_xiaohong"}),
    ("大壮", {"name": "大壮哥", "rank": "王者", "lane": "对抗路", "winrate": 68, "style": "主玩吕布、马超、花木兰。对抗路经验丰富，单挑能力强。会看局势及时支援中路。想找稳定车队冲荣耀。", "contact": "wx_dazhuang"}),
]
for username, data in wzry_subs:
    u = users[username]
    r = submit(u["token"], wzry_id, data)
    if r:
        sid = r["id"]
        print(f"  [OK] 王者荣耀 ← {username}")

# -- 考研 submissions --
study_subs = [
    ("学霸张", {"name": "张同学", "target_school": "清华大学", "major": "计算机科学与技术", "study_hours": 11,
     "weak_subjects": ["政治", "英语"],
     "intro": "我是计算机专业本科生，专业课基础扎实，数学也还可以。目前政治和英语是短板，希望找到同样考计算机的同学一起刷题、分享资料、互相监督早起打卡。", "contact": "wx_xbzhang"}),
    ("学渣李", {"name": "李同学", "target_school": "浙江大学", "major": "软件工程", "study_hours": 8,
     "weak_subjects": ["数学", "英语"],
     "intro": "跨专业考研，数学基础比较薄弱，英语也一般。专业课在自学中。希望能找到有经验的研友交流，最好能一起讨论数学题。", "contact": "wx_xzli"}),
    ("小红", {"name": "红姐", "target_school": "南京大学", "major": "应用心理学", "study_hours": 10,
     "weak_subjects": ["专业课", "数学"],
     "intro": "二战考研，去年差2分上岸。今年重点攻克专业课和数学。自制力强，可以带人早起学习打卡。希望找同样二战或自律的研友。", "contact": "wx_xiaohong2"}),
]
for username, data in study_subs:
    u = users[username]
    r = submit(u["token"], study_id, data)
    if r:
        print(f"  [OK] 考研 ← {username}")

# -- 健身 submissions --
fitness_subs = [
    ("健身王", {"name": "老王", "goal": "增肌", "years": 3, "days_per_week": 5, "time_slot": "晚上(18-21点)",
     "intro": "健身三年，系统训练增肌。目前三大项：卧推100kg，深蹲140kg，硬拉160kg。想找同样喜欢力量训练的朋友搭档训练，互相保护突破瓶颈。", "contact": "wx_jswang"}),
    ("大壮", {"name": "阿壮", "goal": "力量提升", "years": 2, "days_per_week": 4, "time_slot": "晚上(18-21点)",
     "intro": "练了两年，之前主要减脂，现在想提升力量。喜欢功能性训练，最近在学举重。希望找有经验的朋友指导一下。", "contact": "wx_azhuang"}),
    ("小明", {"name": "小明哥", "goal": "减脂", "years": 1, "days_per_week": 3, "time_slot": "清晨(6-8点)",
     "intro": "刚练一年，目前体脂率22%，目标是降到15%。主要做HIIT和有氧，配合力量训练。早鸟打卡！需要减脂搭子互相监督饮食。", "contact": "wx_xiaoming2"}),
]
for username, data in fitness_subs:
    u = users[username]
    r = submit(u["token"], fitness_id, data)
    if r:
        print(f"  [OK] 健身 ← {username}")

# -- 摄影 submissions (draft scenario, still submit a couple) --
photo_subs = [
    ("小红", {"name": "红红爱拍照", "style": "人像摄影", "gear": "Canon R6 + RF 85 f/1.2 + RF 35 f/1.8",
     "experience": 4, "genres": ["人像", "街拍", "宠物"],
     "contact": "wx_hongphoto"}),
    ("学霸张", {"name": "张摄影", "style": "风光摄影", "gear": "Sony A7R5 + 16-35 f/2.8 GM + 70-200 f/2.8 GM",
     "experience": 6, "genres": ["风光", "夜景", "街拍"],
     "contact": "wx_zhangphoto"}),
]
for username, data in photo_subs:
    u = users[username]
    r = submit(u["token"], photo_id, data)
    if r:
        print(f"  [OK] 摄影 ← {username}")

# === PHASE 4: Update tags ===
print("\n[4/5] Updating user tags...")

tags_map = {
    "小明": ["王者荣耀", "打野", "微信区", "减脂"],
    "小红": ["王者荣耀", "辅助", "QQ区", "摄影", "考研"],
    "大壮": ["王者荣耀", "上单", "微信区", "健身", "力量训练"],
    "学霸张": ["考研", "计算机", "摄影", "风光"],
    "学渣李": ["考研", "跨专业", "软件工程"],
    "健身王": ["健身", "增肌", "力量举", "饮食管理"],
}
for username, tags in tags_map.items():
    u = users[username]
    update_tags(u["token"], tags)
    print(f"  [OK] {username} -> {tags}")

# === PHASE 5: Run matching ===
print("\n[5/5] Running matching...")
# Collect all submission IDs per scenario
for sc_id, sc_name in [(wzry_id, "王者荣耀"), (study_id, "考研"), (fitness_id, "健身")]:
    admin_tok = users["管理员"]["token"]
    # Get all submissions for this scenario (admin can see all)
    r = requests.get(f"{API}/submissions/scenario/{sc_id}",
                     headers={**HEADERS, "Authorization": f"Bearer {admin_tok}"}).json()
    print(f"\n  {sc_name}: {len(r)} submissions")
    for sub in r:
        sid = sub["id"]
        owner_id = sub["user_id"]
        # Run matching with the submission owner's token (backend requires ownership)
        owner_token = None
        for name, u in users.items():
            if u["user"]["id"] == owner_id:
                owner_token = u["token"]
                break
        if not owner_token:
            owner_token = admin_tok  # fallback
        result = run_matching(owner_token, sid)
        if result and result.get("matches"):
            print(f"    [OK] {sub['form_data'].get('name', '?')} -> {len(result['matches'])} matches")
        else:
            print(f"    - {sub['form_data'].get('name', '?')} -> no matches (need more participants)")

print("\n" + "=" * 60)
print("  ✅ Demo data seeding complete!")
print("=" * 60)
print()
print("  Demo accounts (password: demo123456):")
print("    小明    xm@demo.com   — 王者+健身")
print("    小红    xh@demo.com   — 王者+考研+摄影")
print("    大壮    dz@demo.com   — 王者+健身")
print("    学霸张  xbz@demo.com  — 考研+摄影")
print("    学渣李  xzl@demo.com  — 考研")
print("    健身王  jsw@demo.com  — 健身")
print("    设计师A dsn@demo.com  — 场景设计者")
print("    管理员  admin@qm.com / admin123")
