"""
main.py — 医院信息系统 FastAPI 应用入口
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import settings
from database import init_db
from routers import (
    admission_router,
    ai_router,
    auth_router,
    charge_router,
    director_router,
    drug_router,
    kiosk_router,
    nurse_router,
    order_router,
    patient_router,
    pharm_router,
    reg_router,
    warehouse_router,
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
| 1 | 门诊挂号管理 | 普通/专家/急诊/专科挂号 |
| 2 | 门诊划价系统 | 中西药处方划价、处方查询 |
| 3 | 门诊收费系统 | 支持单独运行或联网挂号系统 |
| 4 | 药房系统 | 中西药房管理、盘点、退药、销量统计 |
| 5 | 门诊药房发药 | 划价后处方自动推送药房窗口 |
| 6 | 药库管理 | 中药库、西药库出入库 |
| 7 | 出入院管理 | 入院登记、押金、费用清单、出院结算 |
| 8 | 护士工作站 | 床位管理、医嘱管理、一日清单 |
| 9 | 中心药房 | 医嘱发药、摆药单、库存管理 |
| 10 | 检验室收费 | 与医嘱联网 |
| 11 | 手术收费 | 与医嘱联网 |
| 12 | 功能科室收费 | B超/胃镜/放射科，与医嘱联网 |
| 13 | 中医医嘱 | 与医嘱联网 |
| 14 | 院长查询 | 业务报表、财务报表、AI解读 |
| 15 | 触摸屏导诊 | IC卡查询、一日清单、药价公开、科室介绍 |
| AI | AI助手 | 阿里云百炼 Dashscope 智能辅助 |
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ─────────────────────────────────────────────────
# ── 注册路由 ─────────────────────────────────────────────────
for router in [
    auth_router,
    patient_router,
    reg_router,
    drug_router,
    pharm_router,
    warehouse_router,
    admission_router,
    nurse_router,
    order_router,
    charge_router,
    director_router,
    kiosk_router,
    ai_router,
]:
    app.include_router(router)

# 补充处方路由（单独注册）
from routers import pres_router

app.include_router(pres_router)


@app.get("/", tags=["健康检查"])
async def root():
    return {
        "system": "医院信息系统 (HIS)",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


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
