# 从零构建智能医院信息系统（HIS）：架构、流程与实战总结

> 一个覆盖 15 个业务模块、23 张数据表、68 个 API 端点的完整医院信息系统，从门诊挂号到住院结算，从药房库存到 AI 智能辅助，从医护工作台到患者自助门户。

---

## 一、项目概述

**医院信息系统（Hospital Information System，HIS）** 是医院运营的数字中枢。本项目从零搭建了一套 Web 架构的 HIS，后端采用 **Python FastAPI + SQLAlchemy 2.0（异步）+ MySQL**，前端采用 **Vue 3 + Vite + Element Plus**，并集成了 **LangChain / LangGraph 多智能体 AI 引擎**，支持自然语言问诊、处方审核和智能问数。

### 核心数字

| 指标 | 数值 |
|------|------|
| 业务模块 | 15 个 |
| 数据库表 | 23 张 |
| API 端点 | 68 个 |
| 用户角色 | 6 种（admin / doctor / nurse / cashier / pharmacist / patient） |
| 前端页面 | 20+ 个 SFC 组件 |

---

## 二、系统架构总览

```
┌─────────────────────────────────────────────────────┐
│                    前端层 (Vue 3)                     │
│  ┌──────────────┐  ┌──────────────────────────────┐ │
│  │ 医护端 /index │  │ 患者端 /patient              │ │
│  │ 14个功能页面  │  │ 5个自助页面                  │ │
│  └──────────────┘  └──────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│                  API 网关 (FastAPI)                   │
│  ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐ │
│  │挂号  ││处方  ││药房  ││住院  ││收费  ││AI   │ │
│  │路由  ││路由  ││路由  ││路由  ││路由  ││路由  │ │
│  └──────┘└──────┘└──────┘└──────┘└──────┘└──────┘ │
├─────────────────────────────────────────────────────┤
│                    数据层                             │
│  ┌────────────────┐  ┌────────────────────────────┐ │
│  │ MySQL (aiomysql)│  │ Qdrant (向量数据库)        │ │
│  │ 23张业务表      │  │ RAG 知识库检索             │ │
│  └────────────────┘  └────────────────────────────┘ │
│  ┌────────────────┐  ┌────────────────────────────┐ │
│  │ Redis (缓存)    │  │ LangGraph (多智能体引擎)   │ │
│  └────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 技术选型理由

- **FastAPI + 异步 SQLAlchemy**：原生 async/await 支持，与 aiomysql 配合实现非阻塞数据库操作，单进程即可承载高并发
- **单体路由文件**：15 个 APIRouter 集中注册在 `routers.py`，依赖注入（Depends）模式保证鉴权和数据库会话的一致性
- **Vue 3 + Element Plus**：成熟的医疗后台 UI 体系，表格/表单/弹窗等组件开箱即用
- **LangGraph**：多智能体协作框架，Router Agent 自动分类用户意图后分发给 Consultant / Medical / Science / Tool 四个专业 Agent

---

## 三、15 个业务模块全景

### 模块矩阵

| # | 模块 | 路由前缀 | 核心表 | 角色 |
|---|------|---------|--------|------|
| 1 | 认证与权限 | `/api/auth` | users | 全部 |
| 2 | 患者管理 | `/api/patients` | patients | admin/doctor/nurse/cashier |
| 3 | 门诊挂号 | `/api/registrations` | registrations | admin/doctor/cashier |
| 4 | 处方管理 | `/api/prescriptions` | prescriptions, prescription_items | admin/doctor |
| 5 | 药品主档 | `/api/drugs` | drugs | admin/pharmacist |
| 6 | 药房管理 | `/api/pharmacy` | pharmacy_inventory | admin/pharmacist |
| 7 | 药库管理 | `/api/warehouse` | warehouse_inventory, drug_transactions | admin/pharmacist |
| 8 | 住院管理 | `/api/admissions` | admissions, admission_fee_items, beds | admin/nurse/cashier |
| 9 | 护士工作站 | `/api/nurse` | beds, medical_orders, vital_signs | admin/nurse |
| 10 | 医嘱管理 | `/api/orders` | medical_orders | admin/doctor |
| 11 | 特殊收费 | `/api/charges` | special_charges, charge_items | admin/cashier |
| 12 | 院长查询 | `/api/director` | 聚合查询 | admin |
| 13 | 统一收费 | `/api/billing` | billing_records | admin/cashier |
| 14 | AI 助手 | `/api/ai` | ai_sessions | 全部 |
| 15 | 患者自助 | `/api/patient-self` | 归属查询 | patient |

---

## 四、核心业务流程详解

### 4.1 门诊就诊全链路

这是 HIS 系统最核心、最频繁的业务流程。一名患者从进入医院到取药离开，完整的数据链路如下：

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ ① 挂号   │───→│ ② 就诊   │───→│ ③ 开方   │───→│ ④ 收费   │───→│ ⑤ 发药   │
│ 收费处   │    │ 医生站   │    │ 医生站   │    │ 收费处   │    │ 药房     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │                                                   │
     │  ¥5 (普通) / ¥20 (专家)                            │  处方费
     │  ¥15 (急诊) / ¥10 (专科)                           │  药品单价 × 数量
     │                                                   │
     ▼                                                   ▼
┌─────────────────────────────────────────────────────────────┐
│               billing_records (统一收费主表)                 │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ 挂号收费  ¥5.00  │  │ 门诊处方 ¥112.50 │                  │
│  └─────────────────┘  └─────────────────┘                  │
│              今日收入: ¥117.50 (自动汇总)                    │
└─────────────────────────────────────────────────────────────┘
```

**技术实现要点：**

1. **挂号**：`POST /api/registrations` → 根据 `reg_type` 自动匹配挂号费（FEE_MAP），初始状态 `payment_status=PENDING`
2. **缴费**：`PATCH /api/registrations/{id}/pay` → 状态更新为 PAID + 写入 `paid_at` 时间戳 + **事务性写入统一收费主表 `billing_records`**
3. **开方**：`POST /api/prescriptions` → 自动查询药品单价（`drug.retail_price`），计算 `total_amount = Σ(unit_price × quantity)`
4. **处方缴费**：`PATCH /api/prescriptions/{id}/pay` → 状态更新 + 写入 billing_records（通过 `pres.registration.patient_id` 获取患者 ID）
5. **发药**：`PATCH /api/prescriptions/{id}/dispense` → 校验药房库存 → 扣减 `pharmacy_inventory.stock_qty` → 生成 `drug_transactions` 流水

**防重复收费机制：**
```python
# 1. 状态层拦截
if reg.payment_status == PaymentStatus.PAID:
    raise HTTPException(409, "已收费，不可重复")

# 2. 收费主表层拦截
existing = await db.execute(
    select(BillingRecord).where(
        BillingRecord.charge_type == "挂号收费",
        BillingRecord.source_id == reg_id,
        BillingRecord.status == "已收",
    )
)
if existing.scalar_one_or_none():
    raise HTTPException(409, "已生成收费记录")
```

### 4.2 药品供应链：药库 → 药房 → 患者

```
┌──────────────┐     调拨      ┌──────────────┐     发药      ┌──────────────┐
│  药库        │  ─────────→  │  药房        │  ─────────→  │  患者        │
│  warehouse   │              │  pharmacy    │              │  prescription │
│  _inventory  │              │  _inventory  │              │  .dispensed   │
└──────────────┘              └──────────────┘              └──────────────┘
       │                            │
       │ 入库 (stock-in)            │ 盘点 / 退药
       ▼                            ▼
┌─────────────────────────────────────────────────────────┐
│              drug_transactions (出入库流水)              │
│  入库 +100  │  调拨出库 -50  │  调拨入库 +50  │  发药出库 -9 │
└─────────────────────────────────────────────────────────┘
```

**调拨（transfer）流程：**
1. `POST /api/warehouse/transfer` → 校验药库库存是否充足
2. 扣除 `warehouse_inventory.stock_qty`
3. 增加 `pharmacy_inventory.stock_qty`（不存在则新建）
4. 生成 2 条流水：调拨出库（-quantity）+ 调拨入库（+quantity）

### 4.3 住院全流程

```
入院登记 → 押金缴纳 → 医嘱执行 → 每日清单 → 出院结算 → 释放床位
   │                      │                       │
   │ beds.status=OCCUPIED  │ medical_orders        │ beds.status=AVAILABLE
   │                      │ vital_signs           │ admission.settled=True
   ▼                      ▼                       ▼
┌──────────────────────────────────────────────────────────┐
│                billing_records                            │
│                 住院结算 (total_fee)                       │
└──────────────────────────────────────────────────────────┘
```

**出院结算逻辑：**
```python
total = sum(item.amount for item in adm.fee_items)  # 汇总所有费用明细
adm.total_fee = total
adm.discharge_date = now()
adm.settled = True
adm.paid_at = now()

# 写入统一收费主表
BillingRecord(
    charge_type="住院结算",
    source_id=adm.id,
    paid_amount=total,
    ...
)
# 释放床位
bed.status = BedStatus.AVAILABLE
```

### 4.4 AI 智能辅助链路

```
用户消息 → Router Agent (意图分类)
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼         ▼
Consultant  Medical   Science    Tool
 (闲聊)    (诊疗)    (科普)    (数据查询)
              │         │         │
              ▼         ▼         ▼
         search_kb   search_kb  4个工具函数
         drug_interaction       (查数据/统计/报表)
         summarize_patient
              │
              ▼
         Qdrant RAG (向量检索知识库)
              │
              ▼
         LLM 生成回复 → 返回用户
```

**5 个 LangGraph Agent：**

| Agent | 触发条件 | 能力 |
|-------|---------|------|
| Router | 所有请求 | 关键词 + LLM 双重意图分类 |
| Consultant | 日常咨询 | 普通对话，不走 RAG |
| Medical | 症状/处方 | 诊疗分析 + 可调工具 |
| Science | 健康科普 | 自动判断是否需检索 |
| Tool | 数据查询 | 自然语言 → 工具匹配 → 执行 → 回复 |

**3 个 AI 业务融合端点：**

- `POST /api/ai/triage` — 输入症状 → AI 推荐科室/号别/医生
- `POST /api/ai/check-prescription` — 处方提交时自动审核（相互作用/剂量/重复用药），高危弹窗确认
- `POST /api/ai/director-query` — 自然语言问数（"哪个科室最忙？"），AI 预取全量数据后分析回答

---

## 五、统一收费主表设计（核心重构）

### 问题背景

旧系统存在两个关键缺陷：
1. **「今日收入」仅统计挂号费**（如 ¥5 的挂号费），处方收费（¥112.50）未被计入，实际应为 ¥117.50
2. **「收费历史」缺失挂号费记录**，患者就诊-收费全链路断裂（只能看到处方和住院，看不到挂号）

### 解决方案：BillingRecord 统一收费主表

```sql
CREATE TABLE billing_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    bill_no VARCHAR(30) UNIQUE NOT NULL,     -- BILL20260612XXXXXXXX
    charge_type VARCHAR(20) NOT NULL,        -- 挂号收费 / 门诊处方 / 住院结算
    source_id INT NOT NULL,                  -- FK to registrations/prescriptions/admissions
    patient_id INT NOT NULL,                 -- FK to patients
    total_amount DECIMAL(10,2) DEFAULT 0,
    paid_amount DECIMAL(10,2) DEFAULT 0,
    operator_id INT,                         -- FK to users (收费员)
    charge_time DATETIME NOT NULL,           -- 实际收费时间
    status VARCHAR(20) DEFAULT '已收',       -- 已收 / 已退
    remark VARCHAR(200),
    created_at DATETIME DEFAULT NOW()
);
```

**写穿透模式**：所有付费操作在修改源表状态的同时，事务性地写入 `billing_records`：

```
PATCH /registrations/{id}/pay  ──→  reg.payment_status = PAID
                              ──→  INSERT billing_records (挂号收费)

PATCH /prescriptions/{id}/pay ──→  pres.payment_status = PAID
                              ──→  INSERT billing_records (门诊处方)

PATCH /admissions/{id}/discharge → adm.settled = True
                              ──→  INSERT billing_records (住院结算)
```

**收益：**

| 场景 | 旧逻辑 | 新逻辑 |
|------|--------|--------|
| 今日收入统计 | `SUM(registrations.reg_fee)` | `SUM(billing_records.paid_amount) WHERE charge_time=today` |
| 收入拆分 | 不支持 | `SUM() GROUP BY charge_type`（挂号/处方/住院分开展示） |
| 收费历史 | 前端合并 2 个 API（处方+住院） | 单一 `/api/billing/history` 端点 |
| 对账校验 | 无 | `/api/billing/reconciliation` 自动比对 |
| 患者账单 | 需查多个表 | `/api/patient-self/bills` 单表查询 |

---

## 六、双入口门户设计（医护端 + 患者端）

### 设计理念

传统 HIS 仅面向医护人员，患者无法自助查看信息。本次升级将系统定位为 **医护 + 患者共用平台**，采用同一后端 + 两套独立前端 Layout 的架构。

```
登录页 ──→ [🩺 医护登录] ──→ /index (Index.vue)
    │         14 个功能页面，按角色显隐侧边栏菜单
    │
    └──→ [👤 患者入口] ──→ /patient (PatientIndex.vue)
              5 个自助页面：首页/挂号/处方/账单/AI助手
              数据隔离：只能查本人 patient_id 关联的数据
```

### 登录页双 Tab 设计

```html
<!-- 登录页表单区 -->
<div class="entry-tabs">
  <button :class="{ active: tab === 'staff' }">🩺 医护登录</button>
  <button :class="{ active: tab === 'patient' }">👤 患者入口</button>
</div>

<!-- 医护 Tab：原有用户名+密码+快速登录按钮 -->
<!-- 患者 Tab：手机号+密码登录 / 展开注册表单（姓名/性别/身份证/密码） -->
```

### 角色隔离机制

**路由守卫**（`router/index.ts`）：
```typescript
router.beforeEach((to, _from, next) => {
  const role = localStorage.getItem('role')
  // 患者访问医护端 → 重定向到患者端
  if (role === 'patient' && to.path.startsWith('/index')) {
    next('/patient')
    return
  }
  // 医护访问患者端 → 重定向到医护端
  if (role !== 'patient' && to.path.startsWith('/patient')) {
    next('/index')
    return
  }
  next()
})
```

**API 层归属校验**：所有 `/api/patient-self/*` 端点强制 `require_role("patient")`，且只能查询 `patient_id` 与当前用户关联的数据，杜绝 IDOR 漏洞。

**账户接管防护**：患者自助注册始终创建**新的 Patient 记录**，不通过手机号/身份证关联已有档案，防止冒用他人信息查看其病历账单。

### 两种 Layout 的视觉差异

| 特性 | 医护端 (Index.vue) | 患者端 (PatientIndex.vue) |
|------|-------------------|--------------------------|
| 侧边栏色调 | 深蓝 (#0a1929) | 蓝绿 (#0d3b3b) |
| 菜单项数量 | 14 个（按角色动态显隐） | 5 个（固定） |
| 顶部栏强调色 | 蓝色 (#1677ff) | 绿色 (#10b981) |
| 内容区背景 | 蓝灰渐变网格 | 浅灰纯色 |

---

## 七、智能特性清单

### 7.1 收费智能（billing_router）

| 端点 | 功能 | 实现 |
|------|------|------|
| `/api/billing/reconciliation` | 智能对账 | 比较 billing_records 汇总 vs 各源表（reg+pres+adm）汇总，不一致时生成差异明细 |
| `/api/billing/anomalies` | 异常检测 | 大额收费（≥¥5000）标记 + 实付与总额不符标记 |
| `/api/billing/timeline/{id}` | 患者全链路追溯 | 按时间线合并挂号+处方+收费记录 |

**收入拆分可视化**：`DashboardStats` 新增 `today_reg_revenue` / `today_pres_revenue` / `today_adm_revenue` 三个字段，前端 Director.vue 今日收入卡片下展示分类占比：

```
今日收入 ¥117.50
挂号 ¥5 | 处方 ¥112.50 | 住院 ¥0
```

### 7.2 AI 智能（ai_router）

- **智能分诊**：症状描述 → AI 推荐科室 + 号别 + 医生 → 一键填充挂号表单
- **处方审核**：开方确认时自动调用 AI 检查药物相互作用、剂量合理性、重复用药
- **自然语言问数**：院长输入中文问题 → AI 预取今日概况/收入趋势/科室统计 → 数据驱动回答
- **语音输入**：全局按住空格键说话，自动识别填入任意输入框（WebM → 阿里云 Paraformer）

### 7.3 数据完整性

- **防重复收费**：源表状态 + billing_records 存在性双重校验
- **写穿透一致性**：支付操作与 BillingRecord 写入在同一数据库事务中，要么全成功要么全回滚
- **对账校验**：`/api/billing/reconciliation` 每日自动比对，差异 > 0.01 即告警

---

## 八、项目目录结构

```
his-system/
├── main.py              # FastAPI 入口，lifespan + CORS + 15个路由注册
├── config.py            # pydantic-settings 配置单例（.env → Settings）
├── models.py            # 23 张表的 SQLAlchemy ORM 模型
├── schemas.py           # Pydantic v2 请求/响应模型（from_attributes=True）
├── routers.py           # 单体路由文件（~2700 行），15 个 APIRouter
├── auth.py              # JWT 认证（HS256）+ bcrypt + 角色守卫工厂
├── database.py          # 异步 engine（aiomysql）+ sessionmaker + get_db 依赖
├── ai_service.py        # 阿里云 DashScope 集成 + LangGraph 多智能体委托
├── rag_service.py       # RAG 知识库服务（LangChain + Qdrant）
├── ai_engine/           # LangGraph 多智能体引擎包
│   ├── agents.py        # 5 个 Agent 定义 + 4 个工具函数
│   ├── graph.py         # StateGraph 编排（router → 4 leaves）
│   └── connections.py   # Qdrant + Redis 连接管理
├── seed.py              # 数据库初始化种子（科室/用户/药品/床位）
├── docker-compose.yml   # Qdrant(6333) + Redis(6379)
│
└── his-frontend/
    └── src/
        ├── router/index.ts    # 双端路由（/index + /patient）+ 角色守卫
        ├── views/
        │   ├── Login.vue              # 双入口 Tab 登录页
        │   ├── Index.vue              # 医护端 Layout
        │   ├── PatientIndex.vue       # 患者端 Layout
        │   ├── Dashboard.vue          # 医护首页概览
        │   ├── PatientDashboard.vue   # 患者首页
        │   ├── Registration.vue       # 门诊挂号（含 AI 分诊）
        │   ├── Prescription.vue       # 处方管理（含 AI 审方）
        │   ├── Charge.vue             # 收费管理（统一收费历史+待收费）
        │   ├── Director.vue           # 院长查询（含 AI 问数）
        │   ├── AiChat.vue             # AI 助手（多会话管理）
        │   ├── Nurse.vue              # 护士工作站
        │   ├── Admission.vue          # 住院管理
        │   ├── Pharmacy.vue           # 药房管理
        │   ├── Warehouse.vue          # 药库管理
        │   ├── PatientBills.vue       # 患者账单
        │   ├── PatientRegistrations.vue # 患者挂号
        │   ├── PatientPrescriptions.vue # 患者处方
        │   └── ...
        └── components/
            └── VoiceInput.vue    # 全局语音输入组件
```

---

## 九、关键技术决策与踩坑记录

### 9.1 为什么用单体 routers.py？

68 个端点全在 `routers.py`（~2700 行），看似违反"单一职责"。但在 HIS 场景下，所有端点共享相同的依赖注入模式（`get_db` / `get_current_user`）、业务编号生成（`_gen_no`）、异常处理。拆分成多个文件反而增加跨模块引用复杂度。随着端点数量增长，可按模块拆分为 `routers/` 包。

### 9.2 BillingRecord 写穿透 vs 数据库触发器

本方案选择在应用层（支付端点）手动写入 `BillingRecord`，而非使用 MySQL 触发器。原因是：
- 应用层可记录 `operator_id`（收费员）、`remark`（业务单号）等业务上下文
- 错误处理更灵活（409 状态码、中文错误提示）
- 事务保证：BillingRecord 写入和源表状态更新在同一 `AsyncSession` 中

### 9.3 SQLAlchemy 子查询陷阱

在 billing_history 端点中，最初使用 `.subquery()` 包裹 JOIN 后的查询来做聚合，导致 SUM 结果被行膨胀翻倍。最终改为直接在 BillingRecord 上执行聚合查询，只在需要 patient_name/no 筛选时才动态 JOIN Patient 表。

```python
# ❌ 有问题的写法
sum_q = select(...).join(Patient, ...).subquery()
result = select(func.sum(...)).select_from(sum_q)  # 子查询行膨胀

# ✅ 正确写法
result = select(func.sum(BillingRecord.paid_amount))
if patient_name:
    result = result.join(Patient, ...).where(...)
```

### 9.4 FastAPI + 异步数据库的调试

`TestClient` 无法直接测试异步 SQLAlchemy 端点（会抛出 `MissingGreenlet` 异常）。推荐两种调试方式：
- **集成测试**：用 `httpx.AsyncClient` 发送真实 HTTP 请求
- **单元测试**：直接用 `async_sessionmaker` 执行 SQL 验证查询逻辑

---

## 十、启动与演示

```bash
# 1. 克隆项目
cd his-system

# 2. 安装后端依赖
uv sync

# 3. 启动基础设施（Qdrant + Redis）
docker-compose up -d

# 4. 初始化数据库
python seed.py

# 5. 启动后端
python main.py
# → http://localhost:8000

# 6. 启动前端
cd his-frontend
npm install
npm run dev
# → http://localhost:5173
```

**测试账号：**

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | Admin@123 |
| 医生 | doctor1 | Doctor@123 |
| 护士 | nurse1 | Nurse@123 |
| 收费员 | cashier1 | Cashier@123 |
| 药师 | pharmacist1 | Pharma@123 |
| 患者 | 自助注册 | 手机号+密码 |

---

## 十一、后续迭代方向

1. **WebSocket 实时推送**：处方缴费后自动推送至药房发药窗口，取代当前轮询
2. **Redis 缓存层**：高频查询（药品列表、科室列表）接入 Redis，降低 MySQL 压力
3. **Celery 异步任务**：AI 会话标题生成、知识库文档解析等耗时操作异步化
4. **Docker 部署**：前后端容器化 + Nginx 反向代理，支持一键部署
5. **医保接口对接**：与国家医保平台对接，实现实时结算和报销
6. **移动端适配**：患者端支持微信小程序，方便在线挂号和查报告

---

> 本项目从零搭建了一套功能完整的 HIS 系统，涵盖了从门诊到住院、从药品到收费、从 AI 辅助到患者自助的全链路。代码开源于 GitHub，欢迎 Star 和 PR。

🤖 本文由 Claude Code 辅助撰写，项目由南昌师范学院团队开发。
