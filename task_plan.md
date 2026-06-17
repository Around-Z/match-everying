# 任务计划：用户系统 + 管理后台 + 商业化 UI

## 目标
为匹配平台添加完整的用户认证系统、管理后台仪表盘、AI 场景二次编辑功能、以及商业化级别的 UI 设计。

## 当前阶段
阶段 5（新）

## 已完成阶段
- 阶段 1：MVP 后端核心 ✅ — FastAPI + 智谱 embedding + Milvus + DeepSeek
- 阶段 1b：架构切换 ✅ — OpenAI+Pinecone → 智谱+Milvus+DeepSeek

---

## 阶段 5：用户认证系统（JWT）

### 5.1 数据库层
- [ ] 创建 `users` 表（id, email, username, password_hash, role, created_at）
- [ ] 创建 `user_sessions` 表（可选的 token 黑名单/刷新机制）
- [ ] DB 迁移：为现有 submissions 添加 user_id 外键约束

### 5.2 后端 API
- [ ] `POST /api/auth/register` — 注册（email + username + password）
- [ ] `POST /api/auth/login` — 登录，返回 JWT access_token
- [ ] `GET /api/auth/me` — 获取当前用户信息
- [ ] `PUT /api/auth/me` — 更新个人信息
- [ ] JWT 中间件：保护需要登录的路由
- [ ] 角色中间件：`require_role("admin")` 用于管理端点

### 5.3 用户角色
| 角色 | 权限 |
|------|------|
| `participant` | 浏览场景、填写提交、查看自己的匹配结果 |
| `designer` | 上述 + 创建/编辑场景、查看场景统计 |
| `admin` | 上述 + 全局概览、用户管理、场景管理 |

### 5.4 现有 API 改造
- [ ] 提交 API：`user_id` 从 JWT 提取，不再默认 `'anonymous'`
- [ ] 场景 API：`creator_id` 从 JWT 提取
- [ ] 匹配结果 API：添加 `GET /api/matching/my-results` 返回当前用户的所有匹配
- [ ] 提交历史 API：`GET /api/submissions/my` — 当前用户的所有提交

### 5.5 前端页面
- [ ] 登录页 `/login` — 邮箱 + 密码 + 注册链接
- [ ] 注册页 `/register` — 邮箱 + 用户名 + 密码 + 角色选择
- [ ] 用户中心 `/me` — 个人信息、我的场景、我的提交、我的匹配
- [ ] 导航栏：登录/注册按钮 | 用户头像下拉菜单

---

## 阶段 6：场景编辑器（AI 生成 + 手动编辑）

### 6.1 后端
- [ ] `GET /api/scenarios/{id}/edit` — 获取场景完整可编辑数据
- [ ] `PUT /api/scenarios/{id}` — 已支持，需确认 form_schema/match_config/ui_config 均可更新
- [ ] 场景编辑权限校验：仅 creator 和 admin 可编辑

### 6.2 前端 — 场景编辑器页面
- [ ] `/scenarios/{id}/edit` — 可视化场景编辑器
- [ ] 左侧：实时表单预览（根据 form_schema 动态渲染）
- [ ] 右侧：JSON 编辑器（带语法高亮 + 错误提示）
- [ ] 顶部工具栏：保存 | 预览 | 发布 | 返回
- [ ] 发布流程：draft → active（带确认对话框）
- [ ] 编辑历史/撤销（可选，MVP 可跳过）

### 6.3 AI 生成 + 人工编辑 工作流
```
设计者输入自然语言 → DeepSeek 生成 JSON Schema → 预览 → 手动调整 → 发布
                                                         ↓
                                               JSON 编辑器（可编辑每个字段）
```

---

## 阶段 7：管理后台仪表盘

### 7.1 后端 API
- [ ] `GET /api/admin/stats` — 全局统计：
  - 总场景数、活跃场景数
  - 总用户数（按角色分布）
  - 总提交数、总匹配对数
  - 最近 7 天新增数据
- [ ] `GET /api/admin/users` — 用户列表（分页、搜索、按角色筛选）
- [ ] `GET /api/admin/scenarios` — 场景列表（分页、搜索、按状态筛选）
- [ ] `PUT /api/admin/users/{id}/role` — 修改用户角色
- [ ] `DELETE /api/admin/scenarios/{id}` — 删除场景（软删除或硬删除）

### 7.2 前端 — 管理后台
- [ ] `/admin` — 仪表盘首页（统计卡片 + 趋势图表）
- [ ] `/admin/users` — 用户管理（表格 + 角色编辑 + 搜索）
- [ ] `/admin/scenarios` — 场景管理（表格 + 状态筛选 + 操作）
- [ ] `/admin/submissions` — 提交概览（表格 + 按场景筛选）
- [ ] 侧边栏导航：仪表盘 | 用户 | 场景 | 提交

---

## 阶段 8：商业化 UI 升级

### 8.1 设计系统
- [ ] 确定 UI 框架：推荐 shadcn/ui（Radix + Tailwind）或 Ant Design
- [ ] 全局主题：品牌色、暗色模式、字体系统
- [ ] 通用组件库：
  - `Button`（primary/secondary/outline/ghost/danger）
  - `Card`（带标题、描述、操作的卡片容器）
  - `Table`（排序、分页、搜索、行操作）
  - `Modal`（确认对话框、表单弹窗）
  - `Toast`（操作反馈通知）
  - `Badge`/`Tag`（状态标签：draft/active/completed）
  - `Avatar`（用户头像）
  - `DropdownMenu`（用户菜单、操作菜单）
  - `Tabs`（场景详情页的 tab 切换）
  - `Skeleton`（加载占位）

### 8.2 页面美化
- [ ] 首页 `/` — Hero 区 + 场景卡片网格 + 搜索 + 分类筛选
- [ ] 场景详情 `/scenarios/{id}` — Banner + 表单区 + 已参与人数
- [ ] 匹配结果 `/scenarios/{id}/results` — 结果卡片 + 解释 + 联系按钮
- [ ] 场景编辑器 — 左右分栏 + 工具栏
- [ ] 管理后台 — 侧边栏 + 数据卡片 + 表格

### 8.3 响应式设计
- [ ] 移动端适配（≥375px）
- [ ] 平板适配（≥768px）
- [ ] 桌面端优化（≥1024px）

### 8.4 交互细节
- [ ] 页面切换动画（fade/slide）
- [ ] 表单验证实时反馈
- [ ] 加载状态（Skeleton + Spinner）
- [ ] 空状态（插图 + 引导文案）
- [ ] 错误状态（友好提示 + 重试按钮）
- [ ] 成功反馈（Toast 通知）

---

## 技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 认证方案 | JWT (python-jose + passlib) | 无状态、RESTful、前端友好 |
| 前端 UI 框架 | shadcn/ui (Radix + Tailwind) | 现代、可定制、组件丰富 |
| 密码哈希 | bcrypt (passlib) | 行业标准 |
| Token 有效期 | access: 24h, refresh: 7d | MVP 足够，后续可调 |
| 管理后台路由 | `/admin/*` 前缀 | 清晰的权限边界 |
| JSON 编辑器 | react-json-editor 或 Monaco | 语法高亮 + 错误提示 |

---

## 关键问题
1. ~~Pinecone API key~~ → 已解决：切换到 Milvus
2. ~~OpenAI embedding~~ → 已解决：切换到智谱
3. 前端目前使用 Next.js + Tailwind，需要安装 shadcn/ui
4. 用户系统上线后，历史 `anonymous` 数据如何处理

## 遇到的错误
| 错误 | 尝试次数 | 解决方案 |
|------|---------|---------|
|      |         |         |

## 5 月重启检查
| 问题 | 答案 |
|------|------|
| 我在哪里？ | 阶段 5 开始 — 用户认证系统 |
| 我要去哪里？ | 阶段 5 → 6 → 7 → 8 |
| 目标是什么？ | 完整的商业化匹配平台 |
| 我学到了什么？ | 见 findings.md |
| 我做了什么？ | 见 progress.md |
