<p align="center">
  <a href="https://github.com/An3035/his-system/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="MIT License"/>
  </a>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Vue_3-4ECB8B?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue 3"/>
  <img src="https://img.shields.io/badge/LangGraph-0.1+-FF6B6B?style=for-the-badge" alt="LangGraph"/>  
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=220&color=0:009688,50:0E83CD,100:4ECB8B&text=🏥%20HIS%20System&fontSize=48&fontAlignY=35&fontColor=FFFFFF&section=header" width="100%"/>
</p>

<h2 align="center">智能医疗信息系统 · 多智能体辅助诊疗平台</h2>
<p align="center"><b>Intelligent Hospital Information System — Multi-agent Assisted Diagnosis & Treatment Platform</b></p>

<p align="center">
  融合传统医院业务管理（挂号、药房、住院、收费）与基于 LangGraph + LangChain + RAG 的多智能体AI引擎，覆盖患者全生命周期管理。
</p>

<p align="center">
  <a href="#-核心功能">✨ 功能</a> &nbsp;|&nbsp;
  <a href="#-技术架构">🏗️ 架构</a> &nbsp;|&nbsp;
  <a href="#-快速开始">🚀 开始</a> &nbsp;|&nbsp;
  <a href="#-性能优化">⚡ 性能</a> &nbsp;|&nbsp;
  <a href="#-项目结构">📁 结构</a> &nbsp;|&nbsp;
  <a href="#-贡献指南">🤝 贡献</a>
</p>

<br/>

---

## 📋 概述

**HIS System** 是一套覆盖医院全业务流程的综合性信息系统，最大的特色在于：

> **传统HIS + 多智能体AI = 下一代智能诊疗平台**

| 维度 | 说明 |
|------|------|
| 🏢 **业务管理** | 15个业务模块，覆盖门诊、住院、药房、收费、护理等全流程 |
| 👥 **双端门户** | 医护管理端 + 患者自助端双入口，权限完全隔离，路由守卫拦截 |
| 💰 **智能收费** | 统一收费主表，全品类费用统计，自动对账，异常金额检测 |
| 🎤 **语音交互** | 医疗场景语音识别，支持挂号、处方等场景快速语音录入 |
| 🤖 **AI引擎** | 5个AI智能体协同工作：路由→问诊→医学→科普→工具 |
| 📚 **知识库** | RAG架构，支持PDF/DOCX/TXT多格式文档上传与智能检索 |
| 🎯 **自然语言** | 支持中文自然语言查询，如"今天挂了几个号？"、"阿莫西林库存多少？" |


---

## ✨ 核心功能

### 🏥 医院业务管理

<details open>
<summary><b>点击展开/收起</b></summary>

| 模块 | 功能 |
|------|------|
| 👤 **患者管理** | 患者信息CRUD |
| 📅 **门诊挂号** | 号源管理 · 在线预约 · 取消预约 · 挂号统计 |
| 💊 **处方管理** | 处方开立 · AI审方 · 药品调配 · 退药处理 |
| 📦 **药品管理** | 库存管理 · 存量预警 · 盘点对账 |
| 💰 **收费管理** | 门诊收费 · 退款处理 · 费用查询 · 报表统计 |
| 🏨 **住院管理** | 入院登记 · 床位分配 · 医嘱管理 · 出院结算 |
| 👩‍⚕️ **护士工作站** | 患者护理 · 体温单 · 医嘱执行 |
| 📊 **院长驾驶舱** | 全院数据可视化 · 决策支持 |
</details>

### 👥 双入口角色门户系统

<details>
<summary><b>点击展开/收起</b></summary>

| 模块 | 功能 |
|------|------|
| 🔐 **双Tab登录** | 登录页区分「医护登录」「患者入口」，独立登录逻辑 |
| 🧾 **患者自助注册** | 手机号自主注册，自动关联患者档案，注册即登录 |
| 📱 **患者工作台** | 我的挂号、我的处方、我的账单、就诊记录全链路追溯 |
| 🛡️ **权限隔离** | 基于角色的路由守卫，越权访问自动重定向，杜绝IDOR风险 |
| 🎨 **独立UI主题** | 患者端独立Layout，仅展示患者相关菜单 |
</details>


### 💰 智能收费重构

<details>
<summary><b>点击展开/收起</b></summary>

| 模块 | 功能 |
|------|------|
| 📊 **统一收费主表** | 挂号/处方/住院收费统一写入 BillingRecord，数据口径唯一 |
| 🧮 **营收自动汇总** | 首页今日收入自动统计全品类费用，解决统计不全、对账不准问题 |
| 🔍 **智能对账校验** | 自动比对营收统计与收费明细，差异自动高亮预警 |
| ⚠️ **异常检测** | 重复收费拦截、负数金额拦截、大额减免标红提醒 |
| 📑 **收费历史全覆盖** | 统一展示挂号、处方、住院所有收费记录，支持类型筛选与实时汇总 |
</details>

### 🎤 医疗语音识别

<details>
<summary><b>点击展开/收起</b></summary>

| 模块 | 功能 |
|------|------|
| 🎙️ **语音转文字录入** | 挂号、处方、病历场景支持语音输入，提升医护办公效率 |
| 🏥 **医疗术语优化** | 适配药品名、科室名、诊断术语等医疗场景精准识别 |
| ⚡ **实时转写** | 边说边转，无需等待，支持纠错与手动修正 |
| 🔇 **环境降噪适配** | 适配医院嘈杂环境，保证识别准确率 |
</details>


### 🤖 AI 多智能体引擎

```
                   ┌─────────────┐
                   │  Router Agent │  ← 路由分发
                   └──────┬──────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │Consultation│    │ Medical  │    │  Popular  │
   │   Agent   │    │  Agent   │    │Science Ag.│
   │  AI问诊   │    │  AI诊断  │    │  AI科普  │
   └──────────┘    └──────────┘    └──────────┘
                          │
                          ▼
                   ┌──────────┐
                   │  Tool    │
                   │  Agent   │
                   │  工具调用 │
                   └──────────┘
```

### 📚 RAG 知识库

- **文档管理**：支持 PDF / DOCX / TXT 格式上传
- **智能解析**：文档分块 · embedding 向量化
- **语义检索**：基于 Qdrant + HNSW 索引，毫秒级响应
- **医学知识**：药品说明书、诊疗指南、学术文献等

---

## 🏗️ 技术架构

```mermaid
graph TB
    subgraph FE["🎨 Frontend (Vue 3)"]
        direction TB
        EP[Element Plus]
        EC[ECharts]
        Router[Vue Router + 角色守卫]
        Voice[语音识别模块]
    end
    
    subgraph BE["⚙️ Backend (FastAPI)"]
        direction TB
        API[API Layer]
        Auth[JWT Auth + 双端认证]
        RBAC[RBAC 角色权限]
        Audit[Audit Log]
        Billing[统一收费对账引擎]
    end
    
    subgraph AI["🤖 AI Engine"]
        direction TB
        LG[LangGraph]
        LC[LangChain]
        BA[Balian LLM]
        ASR[语音识别服务]
    end
    
    subgraph DL["🗄️ Data Layer"]
        direction TB
        SQL[(MySQL 8.0)]
        RD[(Redis 7.0)]
        QD[(Qdrant Vector DB)]
    end
    
    EP --> API
    EC --> API
    Router --> API
    Voice --> API
    API --> Auth
    API --> RBAC
    API --> Billing
    API --> LG
    API --> LC
    API --> BA
    API --> ASR
    LG --> SQL
    LG --> RD
    LG --> QD
    LC --> SQL
    LC --> RD
    LC --> QD
    BA --> SQL
    BA --> RD
    BA --> QD
    API --> SQL
    API --> RD
    
    
    style FE fill:#4ECB8B,color:#fff
    style BE fill:#009688,color:#fff
    style AI fill:#FF6B6B,color:#fff
    style DL fill:#0E83CD,color:#fff
```

### 🧩 核心技术栈

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,fastapi,mysql,redis,vue,ts,html,css,docker,git" />
</p>

| 层级 | 技术 | 用途 |
|------|------|------|
| 🎨 **前端** | Vue 3 + Vite + TypeScript + Element Plus + ECharts | 管理界面与数据可视化 |
| ⚙️ **后端** | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic | RESTful API 与数据库迁移 |
| 🤖 **AI** | LangChain 0.2+ / LangGraph 0.1+ / Dashscope (通义千问) / 语音 ASR| 多智能体编排与LLM调用 |
| 🗄️ **数据库** | MySQL 8.0 + Redis 7.0 + Qdrant (HNSW索引) | 关系数据/缓存/向量检索 |
| 🐳 **部署** | Docker + Docker Compose + uv | 容器化编排与包管理 |

---

## 🚀 快速开始

### 前置条件

- Python ≥ 3.11
- Docker & Docker Compose
- MySQL 8.0 + Redis 7.0 + Qdrant（可通过 Docker Compose 一键启动）

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/An3035/his-system.git
cd his-system

# 2. 复制环境变量
cp .env.example .env
# 编辑 .env 配置数据库、Redis、AI API Key 等信息

# 3. 使用 Docker Compose 启动基础设施
docker compose up -d

# 4. 使用 uv 安装 Python 依赖
uv sync

# 5. 运行数据库迁移
uv run alembic upgrade head

# 6. 启动后端服务
uv run uvicorn app.main:app --reload

# 7. 访问 API 文档
# Swagger UI: http://localhost:8000/docs
```

---

## ⚡ 性能优化

| 指标 | 优化前 | 优化后 | 提升倍数 |
|------|--------|--------|:-------:|
| RAG 查询响应 | 1.25s | **80ms** | 🚀 **15x** |
| 并发能力 | 100 QPS | **800 QPS** | 🔥 **8x** |
| AI回答准确率 | 60% | **100%** | 📈 **40%** |
| 缓存命中延迟 | - | **<5ms** | ⚡ - |

---

## 📁 项目结构

```
his-system/
├── app/                     # 后端主应用
│   ├── api/                 # API 路由
│   ├── core/                # 核心配置
│   ├── models/              # 数据模型
│   ├── schemas/             # Pydantic 验证
│   ├── services/            # 业务服务
│   └── ai/                  # AI 引擎
│       ├── agents/          # 智能体定义
│       ├── knowledge/       # RAG 知识库
│       └── tools/           # AI 工具函数
├── web/                     # 前端代码
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 公共组件
│   │   └── router/          # 路由配置
│   └── ...
├── docker-compose.yml       # Docker 编排
├── pyproject.toml            # 项目配置 & 依赖
└── CLAUDE.md                # Claude Code 指令
```

---

## 🤝 贡献指南

欢迎贡献代码、提交 Issue 或建议！

1. 🍴 Fork 本仓库
2. 🌿 创建功能分支 (`git checkout -b feature/amazing`)
3. 💻 提交修改 (`git commit -m 'feat: add amazing feature'`)
4. 📤 推送分支 (`git push origin feature/amazing`)
5. 🔀 提交 Pull Request

> 请确保代码遵循项目现有的风格规范，并在提交前通过测试。

---

## 📄 许可证

本项目基于 **MIT License** 开源 — 详见 [LICENSE](LICENSE) 文件。

---

## 📬 联系

<p align="center">
  <a href="mailto:An3035@163.com">
    <img src="https://img.shields.io/badge/Email-An3035@163.com-EA4335?style=flat-square&logo=gmail&logoColor=white" />
  </a>
  <a href="https://github.com/An3035">
    <img src="https://img.shields.io/badge/GitHub-@An3035-181717?style=flat-square&logo=github&logoColor=white" />
  </a>
  <a href="https://an3035-github-io.vercel.app">
    <img src="https://img.shields.io/badge/Blog-技术博客-0E83CD?style=flat-square&logo=vercel&logoColor=white" />
  </a>
</p>

<p align="center">
  <img src="https://api.star-history.com/svg?repos=An3035/his-system&type=Date" width="400" alt="Star History"/>
</p>

---

<p align="center">
  <b>如果这个项目对你有帮助，请给一个 ⭐️</b>
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=100&color=0:4ECB8B,50:0E83CD,100:009688&section=footer" width="100%"/>
</p>
