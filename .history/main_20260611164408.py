"""
main.py — 医院信息系统 FastAPI 应用入口
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

# ========== 新增：导入静态文件组件 ==========
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import settings
from database import init_db
from routers import (
    admission_router,
    ai_router,
    audit_router,
    auth_router,
    charge_router,
    director_router,
    drug_router,
    kb_router,
    kiosk_router,
    nurse_router,
    order_router,
    patient_router,
    pharm_router,
    reg_router,
    warehouse_router,
)

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🏥 医院信息系统启动中...")
    await init_db()
    logger.info(f"✅ HIS 已就绪，监听 {settings.APP_HOST}:{settings.APP_PORT}")
    yield
    logger.info("🛑 HIS 正在关闭...")


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="""
## 医院信息系统 (HIS) API

### 功能模块
| # | 模块 | 说明 |
|---|------|------|
| 1 | 认证与权限 | 多角色登录、JWT认证、权限控制 |
| 2 | 患者管理 | 患者档案创建、查询、修改 |
| 3 | 门诊挂号 | 普通/专家/急诊/专科挂号、挂号收费 |
| 4 | 处方管理 | 医生开方、自动划价、处方查询 |
| 5 | 药品管理 | 药品主档、药房库存、药库出入库 |
| 6 | 出入院管理 | 入院登记、押金管理、一日清单、出院结算 |
| 7 | 护士工作站 | 床位状态看板、医嘱管理、生命体征录入 |
| 8 | 医嘱发药 | 待发药医嘱列表、执行发药、发药历史 |
| 9 | 收费管理 | 门诊处方收费、住院出院结算、收费历史 |
| 10 | 院长查询 | 今日数据概览、收入趋势、科室统计、药品销量 |
| AI | AI助手 | 智能问诊、病历摘要、药物相互作用分析 |
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS 跨域中间件 ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 新增：挂载前端静态文件（核心改动） ==========
# directory="static" 对应我们重命名的 static 文件夹
# html=True 支持SPA前端路由刷新不404
app.mount("/", StaticFiles(directory="static", html=True), name="frontend")

# ── 注册所有业务路由 ─────────────────────────────────────────────────
for router in [
    auth_router,
    patient_router,
    reg_router,
    drug_router,
    pharm_router,
    warehouse_router,
    kiosk_router,
    admission_router,
    nurse_router,
    order_router,
    charge_router,
    director_router,
    ai_router,
    audit_router,
    kb_router,
]:
    app.include_router(router)

# 补充处方路由（单独注册）
from routers import pres_router

app.include_router(pres_router)

# ========== 注释/删除原有根路由接口（冲突点） ==========
# 因为根路径 / 已经交给前端静态文件，这个接口会失效，直接注释
# @app.get("/", tags=["健康检查"])
# async def root():
#     return {
#         "system": "医院信息系统 (HIS)",
#         "version": settings.APP_VERSION,
#         "status": "running",
#         "docs": "/docs",
#     }


@app.get("/health", tags=["健康检查"])
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
