# 发现与决策

## 当前架构（已实施）
| 组件 | 技术 | 状态 |
|------|------|------|
| 嵌入模型 | 智谱AI `embedding-2` (1024维) | ✅ |
| 向量数据库 | Milvus Standalone Docker v2.5.0 | ✅ |
| LLM 匹配解释 | DeepSeek `deepseek-chat` | ✅ |
| LLM UI 生成 | DeepSeek `deepseek-chat` (结构化输出) | 🔧 待实现 |
| 后端 | FastAPI + Uvicorn | ✅ |
| 前端 | Next.js + Tailwind | 🔧 基础框架就绪 |
| 业务数据库 | SQLite (`user.db`) | ✅ |
| 跨场景隔离 | Milvus `scenario_id` 元数据过滤 | ✅ |
| 启动脚本 | `start.bat` / `start.ps1` | ✅ |

## 16 人种子测试结果 (2026-06-16)
| 指标 | 数值 | 评估 |
|------|------|------|
| 组内平均相似度 | 0.7258 | ✅ 良好 |
| 组间平均相似度 | 0.6277 | ⚠️ 偏高 |
| 区分度 | 0.0981 | ⚠️ 低于 0.15 目标 |
| Top-3 准确率 | 72.9% (35/48) | ✅ 可用 |

### 分组表现
| 组 | 组内 avg | 组间 avg | 区分度 | 评价 |
|----|---------|---------|--------|------|
| outdoor | 0.7848 | 0.6769 | 0.1079 | 最好 |
| gaming | 0.6708 | 0.5232 | 0.1476 | 区分度最佳 |
| cooking | 0.7448 | 0.6328 | 0.1120 | 中等 |
| sports | 0.7004 | 0.6541 | 0.0463 | 最差 |

### 分析
- **Sports 组区分度极低**（0.0463）：因为中文健身/跑步词汇与"坚持""热爱"等通用正面词共现率高，与 outdoor 组词汇重叠严重
- **Gaming 组区分度最好**（0.1476）：游戏/二次元词汇独特（"原神""段位""打野"），不容易与其他组混淆
- **区分度低不是模型问题**——测试数据所有 16 人都用"热爱XX"的模板化中文，embedding 看到的结构相似度 > 语义差异
- **提升方向**：让测试数据更差异化（填更具体的、更独特的描述），而非换 embedding 模型

## 新需求：用户系统 + 管理后台

### 用户认证方案
- JWT（python-jose + passlib/bcrypt）
- 三种角色：participant、designer、admin
- Token 有效期：access 24h, refresh 7d
- 现有 `user_id = 'anonymous'` 数据迁移策略：保留历史数据，新提交绑定真实用户

### 场景编辑器方案
- AI 生成 → 人工审核编辑 → 发布
- JSON 编辑器（Monaco Editor） + 实时预览
- 权限：仅 creator 和 admin 可编辑

### 管理后台方案
- `/admin/*` 路由前缀
- 统计卡片 + 用户/场景/提交管理表格
- 侧边栏导航

### UI 框架选择
- shadcn/ui（基于 Radix + Tailwind）—— 和现有 Next.js + Tailwind 完美集成
- 组件库：Card, Table, Modal, Toast, Badge, Avatar, DropdownMenu, Tabs, Skeleton

## pymilvus 3.0 已知坑（已克服）
| 坑 | 现象 | 解决方案 |
|----|------|---------|
| IndexParams 非 dict | `create_index(params=dict)` → ParamError | 导入 `IndexParams`，用 `.add_index()` |
| VARCHAR 主键 | 简单 API 默认 int64 | 用 CollectionSchema + FieldSchema |
| flush 延迟 | insert 成功但查不到 | 每次 upsert/insert 后显式 flush |
| 索引缺失 | 重新创建 collection 后 load 失败 | init_index 中 try/except 自动补建 |

## 技术决策
| 决策 | 选择 | 理由 |
|------|------|------|
| 认证方案 | JWT (python-jose + passlib) | 无状态、RESTful |
| 前端 UI | shadcn/ui (Radix + Tailwind) | 现代、与现有 Next.js 集成 |
| 密码哈希 | bcrypt | 行业标准 |
| JSON 编辑器 | Monaco Editor | 语法高亮 + 错误提示 |
| 后端框架 | FastAPI (保持不变) | 已有完整代码 |

## 资源
- 项目路径：d:\aworkxia\qimo\database\matching-platform\
- DeepSeek API: https://platform.deepseek.com/api-docs
- 智谱 API: https://open.bigmodel.cn/
- Milvus: localhost:19530 (Docker)
- shadcn/ui: https://ui.shadcn.com/
