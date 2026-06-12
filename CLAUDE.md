# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (Python FastAPI)

```bash
# Install dependencies
uv sync
uv sync --group dev

# Start dev server (with auto-reload)
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Initialize database with seed data (drops all tables first)
python seed.py

# Run tests
pytest
```

### Frontend (Vue 3 + Vite)

```bash
cd his-frontend

# Install dependencies
npm install

# Dev server (proxies /api to localhost:8000)
npm run dev

# Production build
npm run build
```

### Database Migrations

```bash
# Generate new migration from model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Code Quality

```bash
ruff check .           # lint
ruff format .          # format (line-length=100)
black .                # format (line-length=100)
mypy .                 # type check
```

## Architecture

This is a **Hospital Information System (HIS)** with 15 business modules covering outpatient registration, prescriptions, pharmacy, inpatient management, nursing, billing, and a director dashboard.

**Stack:** FastAPI (async) + SQLAlchemy 2.0 (aiomysql) + MySQL / Vue 3 + Vite + Element Plus

### Backend (root directory)

All Python source is flat at the project root — no nested packages:

| File | Role |
|------|------|
| `main.py` | FastAPI app entry point, lifespan, CORS, all router registration |
| `config.py` | `pydantic-settings` reads all config from `.env`. Single `Settings` singleton cached via `@lru_cache` |
| `models.py` | All SQLAlchemy ORM models (18 tables): `User`, `Department`, `Doctor`, `Patient`, `Registration`, `Prescription`, `PrescriptionItem`, `Drug`, `PharmacyInventory`, `WarehouseInventory`, `DrugTransaction`, `Bed`, `Admission`, `AdmissionFeeItem`, `MedicalOrder`, `VitalSign`, `ChargeItem`, `SpecialCharge`, `AiSession` |
| `schemas.py` | All Pydantic v2 request/response schemas. Uses `from_attributes=True` on output models to enable ORM-mode serialization |
| `routers.py` | **Monolithic** ~56KB file containing all 15 API routers. Each router is an `APIRouter` instance with its own prefix and tags |
| `auth.py` | JWT creation/verification (HS256), bcrypt password hashing via passlib, `get_current_user` dependency, `require_role(*roles)` factory for role-based guards |
| `database.py` | Async SQLAlchemy engine (aiomysql), `async_sessionmaker`, `get_db` FastAPI dependency (session + commit/rollback/close), `init_db()` for `Base.metadata.create_all` |
| `ai_service.py` | AliCloud Dashscope integration. Four functions: `chat_with_ai`, `summarize_patient_history`, `analyze_drug_interaction`, `interpret_report_data` |
| `seed.py` | Drops all tables, recreates, and inserts starter data: 8 departments, 4 doctors, 5 users, 8 drugs, 11 charge items, 64 beds, 8 pharmacy inventory records, 8 warehouse inventory records |

**Key patterns:**
- **Auth flow:** All protected endpoints depend on `get_current_user` (JWT decode → DB lookup). Role-restricted endpoints use `require_role("admin", "cashier")` etc.
- **Database access:** Inject `AsyncSession` via `Depends(get_db)`. The session auto-commits on success and auto-rollbacks on exception.
- **Router naming:** Each router is a module-level `APIRouter` variable imported into `main.py`. Example: `reg_router = APIRouter(prefix="/api/registrations")`.
- **Business number generation:** `_gen_no(prefix, length)` in routers.py — timestamp + random digits.

### Frontend (`his-frontend/`)

- **Router** (`src/router/index.ts`): All views nested under `/index` as children (layout shell). Auth guard via `localStorage.getItem('token')` — redirects to `/login` if missing.
- **API client** (`src/api/`): Generated from OpenAPI spec via `openapi-typescript-codegen`. Services in `src/api/services/` export typed methods. `src/utils/request.ts` is the Axios instance with Bearer token interceptor.
- **Views** (`src/views/`): 14 Vue SFCs — one per module. Dashboard, Patient, Registration, Drug, Pharmacy, Warehouse, Prescription, AiChat, Admission, Nurse, Pharmacyorder, Charge, Director.
- **UI framework:** Element Plus. `element-plus` imported globally.
- **Vite proxy:** `/api` → `http://127.0.0.1:8000` during development.
- **Build output:** `npm run build` produces static files served by any HTTP server.

### API Modules and Router Prefixes

| # | Module | Prefix | Core tables |
|---|--------|--------|-------------|
| 1 | Auth | `/api/auth` | users |
| 2 | Patient | `/api/patients` | patients |
| 3 | Registration | `/api/registrations` | registrations |
| 4 | Prescription (pricing/payment) | `/api/prescriptions` | prescriptions, prescription_items |
| 5 | Pharmacy | `/api/pharmacy` | pharmacy_inventory |
| 6 | Warehouse | `/api/warehouse` | warehouse_inventory, drug_transactions; 含 stock-in + transfer 调拨 |
| 7 | Drug master | `/api/drugs` | drugs |
| 8 | Public kiosk | `/api/kiosk` | (read-only queries) |
| 9 | Admission | `/api/admissions` | admissions, admission_fee_items, beds |
| 10 | Nurse station | `/api/nurse` | beds, medical_orders, vital_signs (生命体征) |
| 11 | Medical orders | `/api/orders` | medical_orders |
| 12 | Special charges | `/api/charges` | special_charges, charge_items |
| 13 | Director dashboard | `/api/director` | dashboard, revenue-report, department-stats |
| 14 | AI assistant | `/api/ai` | ai_sessions |

### Roles

`admin` / `doctor` / `nurse` / `cashier` / `pharmacist` — stored in `users.role`. Permission checks use `require_role(*roles)` dependency.

### Notable quirks

- **Seed script is destructive:** `seed.py` drops all tables (`Base.metadata.drop_all`) before recreating. Never run against production.
- **Database URL replacement:** `database.py` substitutes `pymysql` → `aiomysql` in the URL string for async engine. The `config.py` `DATABASE_URL` property uses `pymysql` (sync), which Alembic also uses.
- **`routers.py` is very large (~56KB).** Splitting it would require extracting per-module routers into separate files but maintaining consistent dependency patterns.
- **Redis and Celery** are listed in dependencies but no code uses them yet.
- **Frontend API layer** is generated code (`openapi-typescript-codegen`) — hand-editing it will be overwritten on regeneration.
- **Alembic URL** in `alembic.ini` is hardcoded and may differ from `.env` values. The `env.py` reads from `alembic.ini`'s `sqlalchemy.url`, not from `config.py`.

---

## Changelog

### 2026-05-30 — 全局BUG修复（药品联动/护士站/医嘱发药/缴费/院长查询）

**新增模型：**
- `VitalSign` (vital_signs) — 生命体征记录，支持体温/脉搏/呼吸/血压

**新增API端点：**
- `POST /api/warehouse/transfer` — 药库→药房调拨，含库存校验+事务+流水
- `GET /api/nurse/vitals` — 生命体征列表查询（支持分页+按患者筛选）
- `POST /api/nurse/vitals` — 录入生命体征
- `GET /api/director/department-stats` — 科室挂号量统计

**修复后端BUG：**
- `warehouse_inventory` 返回完整 drug 对象而非仅名字
- `dispense_prescription` 增加库存校验 + DrugTransaction 流水 + 防重复发药
- `list_orders` 增加 admission_no 参数支持；修复 `q` 参数在整型ID上使用 ilike 的错误
- `pending-dispense` 改为返回自定义 dict（含患者姓名/编号/性别 + 药品明细），不再依赖 PrescriptionOut schema
- `list_beds` 占用床位增加 patient_name/admission_no 返回

**修复前端BUG：**
- `Nurse.vue` — 订单状态值改为中文匹配后端；`room_no`→`ward`；Tab切换主动加载
- `Warehouse.vue` — 药品列改用对象渲染；新增调拨操作UI
- `Director.vue` — 折线图/柱状图/排行榜改为真实API数据；补充2个统计卡片
- `Charge.vue` — 合并数据改为客户端分页，页码准确；修复 page_size=200 超限导致422错误；错误信息格式化处理数组detail
- `Admission.vue` — 分页改为实际调用后端

**Seed数据补充：**
- 新增 8 条 `PharmacyInventory`（西药房/中药房各4条）
- 新增 8 条 `WarehouseInventory`（西药库/中药库各4条）

**前置条件：** 执行 `python seed.py` 重新初始化数据库后生效。


### 2026-05-31 — AI 智能融合（分诊/问数/审方）

**新增 API 端点：**

| 方法 | 路径 | 功能 | 角色 |
|------|------|------|------|
| POST | `/api/ai/triage` | 智能分诊：根据症状推荐科室/号别/医生 | 所有 |
| POST | `/api/ai/director-query` | 自然语言问数：中文提问→预取全量数据→AI 分析回答 | admin |
| POST | `/api/ai/check-prescription` | 处方审核：检查相互作用/剂量/重复用药 | admin/doctor |

**新增 Schema：**
- `AiTriageRequest` — { symptoms: str }
- `DirectorQueryRequest` — { question: str }
- `PrescriptionCheckItem` — { drug_id, quantity, unit }
- `PrescriptionCheckRequest` — { patient_id?, items[] }

**前端新增功能：**

1. **智能分诊（Registration.vue）**
   - 挂号弹窗内新增「症状描述」输入框 + "🤖 分诊" 按钮
   - AI 返回推荐科室、号别（普通/专家/急诊/专科）、医生
   - "应用"按钮自动填充挂号表单

2. **自然语言院长查询（Director.vue）**
   - 院长驾驶舱新增「🧠 AI 智能问数」卡片
   - 输入中文问题（如"哪个科室最忙？"），AI 预取今日概况+收入趋势+科室统计后回答
   - 内置 4 个快捷提问按钮

3. **处方实时 AI 审核（Prescription.vue）**
   - 点击"确认开立"时自动调 AI 审核处方
   - 高危问题弹出确认框（显示具体风险），医生可选择"仍要开立"或"返回修改"
   - 低风险以消息提示，不阻塞流程

**架构规范：**
- 所有 AI 业务端点统一挂在 `ai_router`（prefix=`/api/ai`）下
- 分诊/审方使用 `chat_with_ai()` 内部调用（内容已在前置环节过滤）
- 院长查询使用 `require_role("admin")` 保护
- 新端点需在 `schemas.py` 定义请求模型，保持 `from_attributes=True` 输出风格


# AI 引擎架构升级：LangChain + LangGraph + Qdrant + Redis (2026-05-31)

## 架构概览

```
用户请求 → API 路由 (routers.py，完全不变)
               ↓
   ┌──────────────────────────────┐
   │  ai_service.py (接口不变)     │ ← 内部委托 LangGraph
   │  rag_service.py (接口不变)    │ ← 内部委托 LangChain+Qdrant
   └──────────┬───────────────────┘
              ↓
   ┌──────────────────────────────┐
   │  ai_engine/ 智能引擎包       │
   │  ├── connections.py          │ Qdrant + Redis 连接管理
   │  ├── agents.py               │ 5 个 Agent 定义 + 4 个工具函数
   │  └── graph.py                │ LangGraph StateGraph 编排
   └──────────┬───────────────────┘
              ↓
   ┌────────────────────┬────────────────────┐
   │  Qdrant 向量数据库  │  Redis 缓存         │
   │  (文档向量检索)     │  (查询结果/会话缓存) │
   └────────────────────┴────────────────────┘
```

## 新增目录与文件

### `ai_engine/` 包 — LangGraph 多智能体引擎

| 文件 | 作用 |
|------|------|
| `__init__.py` | 包入口，导出连接管理函数 |
| `connections.py` | QdrantClient + ConnectionManager 单例，延迟初始化 + 健康检查 |
| `agents.py` | 5 个 Agent 定义（Router/Consultant/Medical/Science/Tool）+ 4 个工具函数 + TOOL_REGISTRY |
| `graph.py` | LangGraph StateGraph 构建，5 个 node 函数 + 条件路由边 |

### `rag_engine.py` — LangChain + Qdrant RAG 引擎

| 组件 | 实现 |
|------|------|
| 文档加载 | `PyPDFLoader` / `Docx2txtLoader` / 纯文本（LangChain DocumentLoader） |
| 文本分块 | `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)` |
| 向量化 | `DashScopeEmbeddings(model="text-embedding-v2")` |
| 向量存储 | `QdrantVectorStore` (langchain-qdrant) |
| Collection | `his_knowledge_base`，COSINE 距离，1536 维，带 document_id payload 索引 |

### 其他新增/修改文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `docker-compose.yml` | 新增 | Qdrant(6333) + Redis(6379) 容器编排 |
| `migrate_kb_to_qdrant.py` | 新增 | MySQL→Qdrant 数据迁移脚本 |
| `pyproject.toml` | 修改 | 添加 langchain/langgraph/qdrant-client/langchain-qdrant 依赖 |
| `.env` | 修改 | 添加 QDRANT_HOST / QDRANT_PORT / QDRANT_COLLECTION |
| `config.py` | 修改 | 添加 Qdrant 配置项 + RAG_CACHE_TTL |
| `ai_service.py` | 修改 | 内部走 LangGraph 多智能体，函数签名完全不变 |
| `rag_service.py` | 修改 | 内部委托 rag_engine.py，类接口完全不变 |
| `redis_cache.py` | 修改 | 添加 get_rag_cache / set_rag_cache / invalidate_rag_cache |

## 5 个 LangGraph Agent

| Agent | 路由条件 | 能力 | 可调用工具 |
|-------|---------|------|-----------|
| **Router** (路由) | 所有请求必经 | 关键词 + LLM 双重意图分类 | - |
| **Consultant** (咨询) | 日常健康咨询/闲聊 | 普通对话，不走 RAG | - |
| **Medical** (医疗) | 症状/处方/患者信息 | 诊疗分析，可调用工具查数据 | search_kb, drug_interaction, summarize_patient |
| **Science** (科普) | 健康科普/医疗政策 | 自动判断是否需要检索知识库 | search_kb |
| **Tool** (工具) | 数据查询/统计/报表 | 自然语言匹配工具 + 执行 + 结果回复 | 4 个工具函数全部可用 |

### Agent 流程

```
Router → 分类意图 → Consultant / Medical / Science / Tool
                      │
              Medical/Science
                  ↓ 需要数据/知识?
              Tool Agent → 结果返回原 Agent → 生成回复
```

### 意图分类

`classify_intent()` 函数在 `agents.py` 中实现：
- 关键词匹配（tool/medical/science 三组关键词）
- LLM 二次确认（当关键词分类为 consult 时）
- 降级默认：consult

## LangGraph StateGraph

定义在 `graph.py` 中：

```python
class AgentState(TypedDict):
    user_message: str
    history: List[dict]
    context_type: str                  # general/patient/drug/report
    context_data: Optional[dict]
    his_system_prompt: str
    user_intent: str                   # consult/medical/science/tool
    routed_agent: str
    tool_calls: List[dict]
    tool_results: List[dict]
    final_response: str
    error: Optional[str]
```

Graph 结构：
- `router` → 条件边（按 intent）→ `consultant` / `medical` / `science` / `tool`
- 所有叶子节点 → `END`

## 降级机制

LangGraph 执行失败时自动降级到直接 Dashscope 调用：

```python
async def chat_with_ai(...):
    try:
        executor = get_agent_executor()
        result = await executor.ainvoke(initial)
        return result["final_response"]
    except Exception:
        return await _fallback_chat(...)  # 直接调 Dashscope
```

## RAG 引擎接口 (rag_engine.RAGEngine)

```python
class RAGEngine:
    def add_document(content: bytes, filename: str, document_id: int, document_title: str) -> int
    def search(query: str, top_k: int = 5) -> List[dict]
    def delete_document(document_id: int)
    def delete_all()
```

返回格式：
```python
# search() 返回
[{"content": "...", "document_title": "...", "score": 0.95}, ...]
```

## Redis 缓存层

| 缓存类型 | 键格式 | TTL | 失效条件 |
|---------|--------|-----|---------|
| RAG 查询 | `rag:query:{sha256(query)[:16]}` | 3600s (1h) | 知识库文档增删时触发 `invalidate_rag_cache()` |
| 知识库搜索 | `kb:search:{sha256(query)[:16]}` | 600s (10min) | 同上 |
| 药物相互作用 | `drug:int:{sha256(drugs)[:16]}` | 3600s | 手动失效 |
| 用户会话 | `session:user:{user_id}` | 1800s | 登出时失效 |
| 患者信息 | `patient:{patient_id}` | 300s | 信息更新时失效 |

## 数据迁移

`python migrate_kb_to_qdrant.py` 将 MySQL 中现有 KnowledgeChunk 数据导入 Qdrant：

```bash
# 正常迁移
python migrate_kb_to_qdrant.py

# 清空后重新导入
python migrate_kb_to_qdrant.py --force

# 仅扫描，不写入
python migrate_kb_to_qdrant.py --dry-run
```

## 基础设施

### Docker Compose
```bash
docker-compose up -d   # 启动 Qdrant (6333) + Redis (6379)
docker-compose down    # 停止
```

### 环境变量 (.env)
```
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=his_knowledge_base
```

## 核心约束（绝对不可违反）

1. **接口不变**：`ai_service.py` 的 5 个函数和 `rag_service.py` 的 `RAGService` 类的方法签名永远保持不变
2. **前端零改动**：所有 API 路径、方法、请求参数、返回格式与升级前完全一致
3. **LangGraph 降级**：Agent 执行失败时必须静默降级到直接 Dashscope 调用，不允许返回错误给用户
4. **Qdrant 连接失败**：RAG 搜索失败时必须返回空列表而不是报错
5. **工具调用安全**：Tool Agent 只读不写，不修改任何 HIS 业务数据


# AI聊天模块开发规范 (2026-05-31)

## 功能概要

AI聊天模块支持多会话管理，每次对话作为一个独立 Session 持久化存储。包含：会话列表、单条/批量删除、重命名、页面刷新后自动恢复上次会话。

---

## 数据模型: `AiSession`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | 自增主键 |
| `user_id` | FK→users.id | 所属用户 |
| `title` | String(200) nullable | AI 自动概括首条用户问题生成（2~5字） |
| `context_type` | String(30) | patient/drug/report/general |
| `context_id` | Integer nullable | 关联业务ID |
| `messages` | Text | JSON数组，每条消息格式见下方 |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 最后更新时间（每次聊天更新） |

### messages JSON 数组格式

```json
[
  {"role": "user",      "content": "用户消息", "time": "2026-05-31T14:30:00"},
  {"role": "assistant", "content": "AI回复",   "time": "2026-05-31T14:30:05"}
]
```

- `role`: `"user"` | `"assistant"`
- `content`: 消息正文
- `time`: ISO 8601 时间戳（后端保存时生成）

---

## API 端点

所有端点在 `routers.py` 的 `ai_router`（prefix=`/api/ai`）中，统一依赖 `get_current_user` 鉴权。

### 聊天

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/ai/chat` | 发送消息并获取 AI 回复 |

**请求体** (`AiChatRequest`):
```json
{
  "message": "用户消息",
  "context_type": "general",
  "context_id": null,
  "history": [],
  "session_id": null
}
```
- `session_id` 为空时创建新会话；非空时续写已有会话
- 续写时，后端从 DB 加载 `session.messages` 作为 AI 上下文，忽略前端传入的 `history`

**响应体** (`AiChatResponse`):
```json
{
  "reply": "AI回复内容",
  "model": "qwen-turbo",
  "rejected": false,
  "session_id": 1
}
```
- `session_id` 固定返回当前会话 ID，前端据此更新 activeSessionId

### 会话 CRUD

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/ai/sessions` | 列出当前用户所有会话（按 `updated_at` 倒序） |
| GET | `/api/ai/sessions/{id}` | 获取指定会话的完整消息列表 |
| PUT | `/api/ai/sessions/{id}` | 重命名会话标题 |
| DELETE | `/api/ai/sessions/{id}` | 删除单个会话 |
| POST | `/api/ai/sessions/batch-delete` | 批量删除会话 |

**`GET /api/ai/sessions` 响应** (`AiSessionOut[]`):
```json
[
  {
    "id": 1,
    "title": "高血压用药注意事项",
    "context_type": "general",
    "message_count": 6,
    "created_at": "2026-05-31T10:00:00",
    "updated_at": "2026-05-31T14:30:00"
  }
]
```

**`GET /api/ai/sessions/{id}` 响应** (`AiSessionDetailOut`):
```json
{
  "id": 1,
  "title": "高血压用药注意事项",
  "messages": [
    {"role": "user", "content": "...", "time": "..."},
    {"role": "assistant", "content": "...", "time": "..."}
  ],
  "created_at": "2026-05-31T10:00:00",
  "updated_at": "2026-05-31T14:30:00"
}
```

**`PUT /api/ai/sessions/{id}` 请求体** (`SessionRenameRequest`):
```json
{"title": "新标题"}
```

**`POST /api/ai/sessions/batch-delete` 请求体** (`BatchDeleteRequest`):
```json
{"ids": [1, 2, 3]}
```

---

## 前端架构 (AiChat.vue)

### 布局结构

```
.ai-root (flex row)
  ├── .ai-sidebar (280px fixed width)
  │   ├── sidebar-header: "新对话" 按钮
  │   ├── sidebar-sessions: 可滚动的会话列表
  │   └── batch-bar: 批量删除栏（多选时显示）
  └── .ai-chat-area (flex:1)
      ├── .ai-topbar: 标题 + 重命名/新对话按钮
      ├── .ai-messages: 消息气泡 + 欢迎屏
      ├── .file-preview-bar: 上传文件预览
      └── .ai-input-area: 输入框 + 功能按钮
```

### 关键状态

| 变量 | 类型 | 作用 |
|------|------|------|
| `sessions` | ref([]) | 会话列表 `AiSessionOut[]` |
| `activeSessionId` | ref(null) | 当前活跃会话 ID，null=新会话 |
| `selection` | ref([]) | 批量选中会话 ID 数组 |
| `messages` | ref([]) | 当前显示的消息列表 |

### 会话恢复机制

1. `onMounted` → fetchSessions() 获取列表
2. 读取 `localStorage.getItem('lastAiSessionId')`
3. 若存在且仍在 sessions 中 → selectSession(id) 加载消息
4. 若不存在 → 显示欢迎屏

### 发送消息流程

```
send()
  ├─ 有 activeSessionId → payload.session_id = activeSessionId
  ├─ 无 activeSessionId → 不传 session_id，后端自动创建新会话
  ├─ POST /api/ai/chat
  ├─ 收到响应 → 更新 activeSessionId（新会话时）
  ├─ 写 localStorage.setItem('lastAiSessionId', id)
  ├─ fetchSessions() 刷新列表
  └─ scrollBottom()
```

---

### 自动标题

- 新会话首次回复后，后台异步调用 AI（`chat_with_ai`）用 `"用2到5个字概括以下用户问题的核心主题"` 生成极短标题，不拖慢首次响应
- AI 完成前先用用户消息前20字占位
- AI 失败时降级为用户消息前20字
- 前端列表中无标题时显示灰色斜体「新会话」

### 操作约束

- AI 回复中（`loading=true`）禁止切换会话和创建新对话
- 删除当前活跃会话时自动重置为新会话状态
- 批量删除若包含当前活跃会话也自动重置

### 侧栏交互

- 侧栏支持折叠/展开（◀/▶ 按钮），状态持久化到 `localStorage`
- 会话列表支持搜索过滤（按标题实时匹配）
- 复选框常显半透明，hover/active 时全透明
- 支持「加载更多」分页（后端 page_size=30，前端追加）

### 内联重命名

- 侧栏双击标题或顶栏 ✏️ 按钮 → 原地变成输入框
- 回车或失焦保存，Escape 取消

### 删除 Loading

- 删除按钮在请求期间显示 mini-spinner，禁用重复点击
- 批量删除同样有 loading 状态

---

## 会话与历史记录的兼容性

### 旧数据迁移

本次新增 `title` 和 `updated_at` 列。旧数据中：
- `title` 为 NULL → 前端显示「新会话」
- `updated_at` 为 NULL → 用 `created_at` 排序兜底（SQLAlchemy default=now 处理）

### 消息格式兼容

旧消息无 `time` 字段 → 前端 `formatMsgTime()` 返回当前时间兜底，不报错。

---

## 涉及文件清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `models.py` | 修改 | AiSession 增加 `title`、`updated_at` 列 |
| `schemas.py` | 修改 | 新增 AiSessionOut/AiSessionDetailOut/SessionRenameRequest/BatchDeleteRequest；AiChatRequest/Response 增加 session_id |
| `routers.py` | 修改 | /api/ai/chat 支持 session_id + 后台异步生成标题；新增 5 个会话管理端点 + 分页 |
| `his-frontend/src/views/AiChat.vue` | 重写 | 会话侧栏折叠/搜索/分页、复选框常显、内联重命名、删除 loading


### 2026-06-07 — 全局语音输入（按住空格说话）

**新增API端点：**

| 方法 | 路径 | 功能 | 角色 |
|------|------|------|------|
| POST | `/api/ai/asr` | 语音识别：接收WebM音频，返回识别文本 | 所有登录用户 |

**新增Schema：**
- `AsrResponse` — { text: str, duration: Optional[float] }

**新增后端函数：**
- `ai_service.py` → `asr_transcribe(audio_data, filename)` — 调用阿里云百炼 Paraformer（`dashscope.audio.asr.Recognition`），写入临时WAV文件后识别

**前端新增组件：**

1. **VoiceInput.vue**（`his-frontend/src/components/VoiceInput.vue`）
   - 全局挂载于 `App.vue`，无侵入，不破坏任何现有功能
   - 按住空格键 → 自动检测当前聚焦输入框 → 开始录音
   - 松开空格 → 停止录音 → 发送到 `/api/ai/asr` → 文本自动填入光标位置
   - 录音时输入框下方显示动态波形条纹（CSS动画，高度随实时音量变化）
   - 录音中切换焦点输入框自动跟随
   - 优雅降级：浏览器不支持 MediaRecorder 时静默禁用
   - 零新 npm 依赖（浏览器原生 MediaRecorder + AudioContext）

2. **工具函数** `utils/request.ts` → `asrRecognize(audioBlob)` — FormData 上传音频

**技术细节：**
- 音频格式：WebM（16kHz 单声道），通过浏览器 MediaRecorder API 采集
- 音量分析：AudioContext + AnalyserNode（fftSize=256），每80ms采样
- 最短录音时长 0.5s，最长 60s（自动截断）
- 错误处理：权限拒绝/无麦克风/网络错误/识别失败均有中文提示

**使用方式：**
- 任何页面的任何输入框聚焦 → 按住空格说话 → 松开即填入
- Element Plus 的 el-input/el-textarea 自动兼容（组件内部查询 `.el-input input` 选择器）

**涉及文件：**

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `schemas.py` | 修改 | 新增 `AsrResponse` |
| `ai_service.py` | 修改 | 新增 `asr_transcribe()` + 导入 `Recognition`/`tempfile` |
| `routers.py` | 修改 | 新增 `POST /api/ai/asr` 端点 + 导入 `File`/`asr_transcribe` |
| `his-frontend/src/utils/request.ts` | 修改 | 新增 `asrRecognize()` |
| `his-frontend/src/components/VoiceInput.vue` | 新增 | 全局语音输入组件 |
| `his-frontend/src/App.vue` | 修改 | 注册 VoiceInput 组件 |


### 2026-06-12 — 收费模块统一修复与智能增强

**核心问题：**
1. 首页「今日收入」仅统计挂号费（15元），未包含处方收费（114.45元），实际应为 129.45 元
2. 「收费历史」列表缺失挂号费记录，就诊-收费全链路无法追溯（挂号→处方→结算不连贯）

**解决方案：** 新增统一收费主表 `BillingRecord`，所有支付操作（挂号缴费、处方缴费、出院结算）事务性写入该表，看板统计、收费历史、待收费列表均从此表统一查询。

---

**新增数据模型：**

- `BillingRecord` (billing_records) — 统一收费主表
  - `bill_no` — 收费单号（UNIQUE，格式 BILL20260612XXXXXX）
  - `charge_type` — 收费类型：`"挂号收费"` / `"门诊处方"` / `"住院结算"`
  - `source_id` — 源表主键（registrations.id / prescriptions.id / admissions.id）
  - `patient_id` — FK → patients.id
  - `total_amount` / `paid_amount` — 总金额 / 实付金额（DECIMAL(10,2)）
  - `operator_id` — FK → users.id（收费员）
  - `charge_time` — 实际收费时间
  - `status` — `"已收"` / `"已退"`
  - `remark` — 备注（自动记录业务单号）

**现有模型新增字段：**
- `Registration.paid_at` — 挂号缴费时间（nullable DateTime）
- `Prescription.paid_at` — 处方缴费时间（nullable DateTime）
- `Admission.paid_at` — 住院结算时间（nullable DateTime）

---

**新增 API 端点（billing_router，prefix=`/api/billing`）：**

| 方法 | 路径 | 功能 | 角色 |
|------|------|------|------|
| GET | `/api/billing/history` | 统一收费历史查询（含挂号+处方+住院），支持按类型/患者/日期筛选，自动返回汇总金额 | 所有登录用户 |
| GET | `/api/billing/pending` | 统一待收费列表（UNION 挂号PENDING + 处方PENDING + 住院未结算） | 所有登录用户 |
| GET | `/api/billing/timeline/{patient_id}` | 患者全链路收费追溯，按时间线排序 | 所有登录用户 |
| GET | `/api/billing/reconciliation` | 智能对账：比较统一收费表 vs 各源表汇总，标记差异 | admin |
| GET | `/api/billing/anomalies` | 异常检测：大额收费(≥5000)、实付与总额不符、可疑重复 | admin |

---

**修改 API 端点（支付端点增加 BillingRecord 写穿透）：**

| 端点 | 变更 |
|------|------|
| `PATCH /api/registrations/{id}/pay` | 增加 `paid_at` 赋值 + 写入 BillingRecord(charge_type="挂号收费") + 重复收费 409 检测；参数改为 `current_user` 记录操作人 |
| `PATCH /api/prescriptions/{id}/pay` | 增加 `paid_at` 赋值 + 写入 BillingRecord(charge_type="门诊处方") + SELECTINLOAD registration 获取 patient_id + 重复收费 409 检测 |
| `PATCH /api/admissions/{id}/discharge` | 增加 `paid_at` 赋值 + 写入 BillingRecord(charge_type="住院结算") + 重复结算 409 检测 |
| `GET /api/director/dashboard` | `today_revenue` 改为从 BillingRecord 按日期聚合；新增 `today_reg_revenue` / `today_pres_revenue` / `today_adm_revenue` 拆分字段 |
| `GET /api/director/revenue-report` | 改为从 BillingRecord 按日期聚合 |
| `POST /api/ai/director-query` | 收入数据改为从 BillingRecord 获取 |

---

**新增 Schema：**
- `BillingRecordOut` — 收费记录输出（含 patient_name/no/gender/age/ref_no）
- `PendingChargeOut` — 待收费项输出（type / charge_type_label / no / 金额等）
- `ReconciliationResult` — 对账结果 {date, dashboard_total, billing_total, difference, matched, details}
- `BillingSummary` — 汇总 {total_amount, count, by_type}
- `DashboardStats` 扩展 — 新增 `today_reg_revenue`, `today_pres_revenue`, `today_adm_revenue`（默认 0，向后兼容）

---

**前端变更：**

1. **Charge.vue — 全面重构**
   - 待收费 Tab：调用 `/api/billing/pending`（单一端点），新增「挂号收费」类型（橙色 warning tag）
   - 收费历史 Tab：调用 `/api/billing/history`（单一端点），新增：
     - 收费类型筛选下拉框（全部/挂号收费/门诊处方/住院结算）
     - 列表顶部绿色汇总栏：显示当前筛选结果的总金额 + 各类型分项
     - 「挂号收费」以 warning 色 tag 展示
     - 大额收费（≥5000）以红色高亮 + danger tag 标注
     - `charge_time` 直接使用 `BillingRecord.charge_time`
   - 收费弹窗：支持挂号费类型，调用 `/api/registrations/{id}/pay`
   - 错误处理：HTTP 409 → "该记录已收费，不可重复收费"

2. **Director.vue — 收入拆分展示**
   - 今日收入卡片下新增 breakdown：`挂号 ¥X | 处方 ¥Y | 住院 ¥Z`
   - 数据来自 DashboardStats 新增的 `today_reg_revenue` 等字段

3. **Dashboard.vue — 无需改动**（`today_revenue` 自动获取修正后的汇总值）

---

**数据库迁移：**

新建 `BillingRecord` 表（含 `bill_no` UNIQUE 约束和 `patient_id` / `charge_time` 索引），并为 `registrations` / `prescriptions` / `admissions` 分别新增 `paid_at` 列。迁移脚本需回填历史已收数据到 `billing_records` 表。

```bash
alembic revision --autogenerate -m "add billing_records and paid_at columns"
alembic upgrade head
```

---

**重复收费防护机制：**
- 数据库层：`billing_records` 表按 `(charge_type, source_id, status)` 建立唯一约束
- 应用层：支付端点在创建 BillingRecord 前先 SELECT 检查是否已存在，已存在则返回 409

---

**后续扩展指南（新增收费类型）：**
1. 在 BillingRecord.charge_type 中使用新的类型字符串
2. 在对应的支付端点中加入 BillingRecord 写入逻辑（参考 pay_registration 模式）
3. 确保 source_id 指向正确的源表主键
4. 在 `/api/billing/pending` 中 UNION 新的待收费数据源
5. 前端 Charge.vue 的 type tag 映射中添加新类型对应的颜色

---

**涉及文件清单：**

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `models.py` | 修改 | 新增 BillingRecord 模型；Registration/Prescription/Admission 增加 paid_at |
| `schemas.py` | 修改 | 新增 BillingRecordOut / PendingChargeOut / ReconciliationResult / BillingSummary；扩展 DashboardStats |
| `routers.py` | 修改 | 新增 billing_router（5个端点）；修改 3 个支付端点（写穿透）；修改 dashboard/revenue-report/director-query |
| `main.py` | 修改 | 注册 billing_router |
| `his-frontend/src/views/Charge.vue` | 重写 | 统一收费端点 + 挂号类型 + 筛选汇总 + 大额标注 |
| `his-frontend/src/views/Director.vue` | 修改 | 今日收入拆分展示 |


### 2026-06-12 — 双入口门户：患者自助端 + 登录页重构

**背景：** 系统原仅面向医护人员，登录页只有三种快速登录方式。现将系统定位为医护+患者共用平台，采用双入口架构（同一后端，两套前端 Layout）。

---

**数据模型变更：**

- `User` 新增 `patient_id` — FK → patients.id（nullable，仅 role="patient" 时有关联）

---

**新增 API 端点：**

| 方法 | 路径 | 功能 | 角色 |
|------|------|------|------|
| POST | `/api/auth/patient-register` | 患者自助注册（创建 Patient + User，注册即登录返回 token） | 无需登录 |
| GET | `/api/patient-self/profile` | 获取当前患者基本信息 | patient |
| GET | `/api/patient-self/registrations` | 我的挂号记录 | patient |
| GET | `/api/patient-self/prescriptions` | 我的处方记录（含药品明细） | patient |
| GET | `/api/patient-self/bills` | 我的账单（从统一收费主表查询） | patient |
| GET | `/api/patient-self/timeline` | 就诊时间线（挂号+处方+账单合并排序） | patient |

**患者自助 API 安全约束：**
- 所有 `/api/patient-self/*` 端点强制 `require_role("patient")` + 数据归属校验
- 患者只能查看 `patient_id` 与自身关联的数据，不可跨患者查询
- `GET /api/auth/me` 返回增加 `role` 和 `patient_id`，前端据此判断跳转路径

---

**前端架构变更：**

1. **Login.vue — 双入口 Tab 切换**
   - 顶部双 Tab：「🩺 医护登录」/「👤 患者入口」
   - 医护 Tab：保留原有用户名+密码+快速登录按钮
   - 患者 Tab：手机号+密码登录模式 +「立即注册」展开注册表单（姓名/性别/身份证/密码）
   - 注册即登录，自动跳转患者端
   - 登录后根据 role 分流：`patient` → `/patient`，其他 → `/index`

2. **PatientIndex.vue — 患者端 Layout（新建）**
   - 蓝绿色温暖调侧边栏，菜单项：
     - 🏠 首页概览 (`/patient/dashboard`)
     - 📋 我的挂号 (`/patient/registrations`)
     - 📝 我的处方 (`/patient/prescriptions`)
     - 💰 我的账单 (`/patient/bills`)
     - 🤖 AI 健康助手 (`/patient/aichat`)
   - 复用 Index.vue 的 Layout 结构，样式独立

3. **患者端页面（4个新建 SFC）：**

| 文件 | 路由 | 功能 |
|------|------|------|
| `PatientDashboard.vue` | `/patient/dashboard` | 个人信息卡片 + 快捷统计 + 近期就诊时间线 |
| `PatientRegistrations.vue` | `/patient/registrations` | 挂号记录列表（科室/医生/状态/费用） |
| `PatientPrescriptions.vue` | `/patient/prescriptions` | 处方列表（药品明细/收费/发药状态） |
| `PatientBills.vue` | `/patient/bills` | 账单列表（类型/金额/状态/时间）+ 合计金额 |

4. **路由变更（`router/index.ts`）：**
   - 新增 `/patient` 路由组（PatientIndex layout + 5 子路由）
   - 路由守卫按 `role` 隔离：患者访问 `/index/*` → 重定向 `/patient`；医护访问 `/patient/*` → 重定向 `/index`

---

**角色体系（更新后）：**

| 角色 | 登录后入口 | 权限范围 |
|------|-----------|---------|
| `admin` | `/index` | 全部功能 |
| `doctor` | `/index` | 患者管理/挂号/处方/AI助手 |
| `nurse` | `/index` | 患者管理/住院管理/护士工作站 |
| `cashier` | `/index` | 患者管理/挂号/收费管理 |
| `pharmacist` | `/index` | 药品/药房/药库/医嘱发药/AI助手 |
| `patient` | `/patient` | **仅**：我的信息/挂号/处方/账单/AI助手 |

---

**涉及文件清单：**

| 文件 | 变更 | 说明 |
|------|------|------|
| `models.py` | 修改 | User 增加 `patient_id` FK |
| `schemas.py` | 修改 | 新增 PatientRegisterRequest + 患者自助输出 schemas；UserOut 增加 patient_id |
| `routers.py` | 修改 | 新增 POST /api/auth/patient-register + patient_self_router（5端点） |
| `main.py` | 修改 | 注册 patient_self_router |
| `his-frontend/src/views/Login.vue` | 重写 | 双入口 Tab + 患者注册表单 |
| `his-frontend/src/views/PatientIndex.vue` | **新建** | 患者端 Layout |
| `his-frontend/src/views/PatientDashboard.vue` | **新建** | 患者首页 |
| `his-frontend/src/views/PatientRegistrations.vue` | **新建** | 我的挂号 |
| `his-frontend/src/views/PatientPrescriptions.vue` | **新建** | 我的处方 |
| `his-frontend/src/views/PatientBills.vue` | **新建** | 我的账单 |
| `his-frontend/src/router/index.ts` | 修改 | 新增患者端路由 + 角色隔离守卫 |
