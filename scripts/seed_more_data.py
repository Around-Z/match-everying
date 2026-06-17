"""Add more diverse test data to existing scenarios."""
import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API = 'http://localhost:8001/api'
H = {'Content-Type': 'application/json'}

def api(method, path, token=None, **kw):
    headers = dict(H)
    if token: headers['Authorization'] = f'Bearer {token}'
    r = requests.request(method, f'{API}{path}', headers=headers, timeout=30, **kw)
    if r.status_code == 204:
        return {}
    return r.json()

# ===== Register 6 more users =====
print('[1] Creating more users...')
new_users = []
users_to_create = [
    ('电竞高手', 'dj@demo.com', 'wx_dj001', ['王者荣耀','打野','巅峰2000']),
    ('中路法王', 'zl@demo.com', 'wx_zl001', ['王者荣耀','中路','法师']),
    ('考研人甲', 'kyj@demo.com', 'wx_kyjia', ['考研','数学','早起打卡']),
    ('考研人乙', 'kyy@demo.com', 'wx_kyyi', ['考研','英语','资料分享']),
    ('铁馆老炮', 'tglp@demo.com', 'wx_tg666', ['健身','健美','备赛']),
    ('瑜伽达人', 'yjdr@demo.com', 'wx_yj888', ['健身','瑜伽','柔韧性']),
]
for name, email, contact, tags in users_to_create:
    r = api('POST', '/auth/register', json={
        'email': email, 'username': name, 'password': 'demo123456',
        'contact_info': contact, 'role': 'participant',
    })
    if r.get('access_token'):
        new_users.append({'name': name, 'token': r['access_token'], 'user': r['user'], 'tags': tags})
        print(f'  [OK] {name}')
    else:
        r2 = api('POST', '/auth/login', json={'email': email, 'password': 'demo123456'})
        if r2.get('access_token'):
            new_users.append({'name': name, 'token': r2['access_token'], 'user': r2['user'], 'tags': tags})
            print(f'  [OK] {name} (existing)')

# ===== Get scenarios =====
print('[2] Getting scenarios...')
scenarios = api('GET', '/scenarios')
active = [s for s in scenarios if s['status'] == 'active']
print(f'  Found {len(scenarios)} scenarios ({len(active)} active)')

# ===== Login existing users =====
print('[3] Logging in existing users...')
old_users = {}
for email, name in [
    ('xm@demo.com','小明'), ('xh@demo.com','小红'), ('dz@demo.com','大壮'),
    ('xbz@demo.com','学霸张'), ('xzl@demo.com','学渣李'), ('jsw@demo.com','健身王'),
]:
    r = api('POST', '/auth/login', json={'email': email, 'password': 'demo123456'})
    if r.get('access_token'):
        old_users[name] = {'token': r['access_token'], 'user': r['user']}

all_users = {u['name']: u for u in new_users}
all_users.update(old_users)

# ===== Map scenario names to IDs =====
sc_map = {}
for s in scenarios:
    name = s['name']
    if '王者' in name: sc_map['wzry'] = s['id']
    elif '考研' in name and '学习' in name: sc_map['study'] = s['id']
    elif '健身' in name: sc_map['fitness'] = s['id']
    elif '摄影' in name: sc_map['photo'] = s['id']
    elif '情感' in name: sc_map['emotion'] = s['id']

# ===== Submissions =====
submissions = {
    'wzry': [
        ('电竞高手', {'name':'战神电','rank':'王者','lane':'打野','winrate':72,'style':'主玩澜、镜、裴擒虎。巅峰2000分打野，节奏压制型打法，前期入侵野区凶狠。擅长配合中辅联动。需要节奏一致的队友冲荣耀。','contact':'wx_dj001'}),
        ('中路法王', {'name':'法王在线','rank':'星耀','lane':'中路','winrate':65,'style':'主玩不知火舞、貂蝉、安琪拉。中路支援速度快，单杀能力强。擅长游走帮打野建立优势。需要懂配合的打野双排。','contact':'wx_zl001'}),
        ('电竞高手', {'name':'疯狂输出','rank':'钻石','lane':'发育路','winrate':58,'style':'主玩孙尚香、马可波罗。发育路稳扎稳打，后期输出爆炸。会看地图走位，团战站位好。寻稳定辅助搭档。','contact':'wx_dj002'}),
    ],
    'study': [
        ('考研人甲', {'name':'数学钉子户','target_school':'复旦大学','major':'金融学','study_hours':10,'weak_subjects':['数学','政治'],'intro':'跨考金融，数学是最大短板。自制力超强，每天6点起床学习打卡。希望找到同样早起、能互相讲题的研友。','contact':'wx_kyjia'}),
        ('考研人乙', {'name':'英语困难户','target_school':'上海交通大学','major':'机械工程','study_hours':9,'weak_subjects':['英语','专业课'],'intro':'本专业考研，专业课还行但英语太差。需要英语好的研友交流学习方法和作文互改。有大量考研资料可分享。','contact':'wx_kyyi'}),
        ('考研人甲', {'name':'全科学霸','target_school':'北京大学','major':'法学','study_hours':12,'weak_subjects':['政治'],'intro':'法硕考研，每天学习12h+。除政治外各科均衡。可以辅导数学和英语，需要政治好的搭档互相督促进步。','contact':'wx_kyjia2'}),
    ],
    'fitness': [
        ('铁馆老炮', {'name':'老炮不认输','goal':'增肌','years':8,'days_per_week':6,'time_slot':'晚上(18-21点)','intro':'健身八年，系统训练经历丰富。三大项：卧推130kg，深蹲180kg，硬拉220kg。参加过省级健美比赛。可以带徒弟。','contact':'wx_tg666'}),
        ('瑜伽达人', {'name':'柔韧我最强','goal':'塑形','years':4,'days_per_week':5,'time_slot':'清晨(6-8点)','intro':'四年瑜伽+普拉提经验。主要做体态矫正和柔韧性训练。也做轻量力量训练维持线条。晨练打卡达人！','contact':'wx_yj888'}),
        ('铁馆老炮', {'name':'减脂ing','goal':'减脂','years':1,'days_per_week':4,'time_slot':'中午(12-14点)','intro':'刚开始系统健身，目前体脂率25%，目标是降到18%。做力量+HIIT训练。需要减脂搭子互相监督饮食打卡。','contact':'wx_tg6662'}),
    ],
    'photo': [
        ('瑜伽达人', {'name':'光影捕手','style':'街拍摄影','gear':'Fujifilm X-T5 + 23mm f/1.4 + 56mm f/1.2','experience':3,'genres':['街拍','人像','夜景'],'contact':'wx_yjphoto'}),
        ('中路法王', {'name':'风光摄影师','style':'风光摄影','gear':'Nikon Z8 + 14-24 f/2.8 + 24-120 f/4','experience':5,'genres':['风光','夜景','街拍'],'contact':'wx_zlphoto'}),
        ('考研人乙', {'name':'人像大师','style':'人像摄影','gear':'Canon R5 + RF 50 f/1.2 + RF 85 f/1.2 DS','experience':7,'genres':['人像','活动','宠物'],'contact':'wx_kyyphoto'}),
    ],
    'emotion': [
        ('考研人乙', {'name':'寻觅真心','gender':'男','expectation':'希望找到真诚善良、有共同兴趣的另一半。平时喜欢看书、旅行、摄影。认为感情中最重要的是沟通和信任。期待两个人一起成长。'}),
        ('瑜伽达人', {'name':'温暖如初','gender':'女','expectation':'喜欢阳光开朗、有责任心的男生。平时健身瑜伽，也爱做饭。希望对方也能热爱生活，愿意一起分享每天的喜怒哀乐。'}),
        ('考研人甲', {'name':'星河万里','gender':'男','expectation':'感性的人，相信缘分。喜欢听音乐、看电影、散步。期待遇到那个不需要太多言语就能懂彼此的人。'}),
    ],
}

print('[4] Creating submissions...')
all_sub_ids = []
for scenario_key, subs in submissions.items():
    sid = sc_map.get(scenario_key)
    if not sid:
        print(f'  [SKIP] {scenario_key} - not found')
        continue
    for username, data in subs:
        u = all_users.get(username)
        if not u:
            print(f'  [SKIP] {username} not in users')
            continue
        r = api('POST', '/submissions', token=u['token'], json={
            'scenario_id': sid, 'form_data': data,
        })
        if r.get('id'):
            all_sub_ids.append((r['id'], u['token']))
            print(f'  [OK] {scenario_key} <- {username} ({data.get("name","?")})')
        else:
            print(f'  [FAIL] {scenario_key} <- {username}: {r.get("detail",r)}')

# ===== Update user tags =====
print('[5] Updating user tags...')
for u in new_users:
    requests.put(f'{API}/auth/me', headers={**H, 'Authorization': f"Bearer {u['token']}"},
                 json={'tags': u['tags']})
    print(f'  [OK] {u["name"]} -> {u["tags"]}')

# ===== Run matching =====
print('[6] Running matching...')
for sub_id, token in all_sub_ids:
    time.sleep(0.3)  # rate limit
    r = requests.post(f'{API}/matching/run/{sub_id}',
                      headers={**H, 'Authorization': f'Bearer {token}'})
    if r.status_code == 200:
        data = r.json()
        n = len(data.get('matches', []))
        if n > 0:
            print(f'  [OK] {sub_id[:8]}... -> {n} matches')
        else:
            print(f'  - {sub_id[:8]}... -> 0 matches')
    else:
        err = r.json().get('detail', r.text)[:60]
        print(f'  [ERR] {sub_id[:8]}... -> {err}')

print(f'\nDone! {len(all_sub_ids)} new submissions created.')
print(f'Total users: {len(all_users) + len(new_users)}')
