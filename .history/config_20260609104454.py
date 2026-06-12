"""
config.py — 医院信息系统全局配置
所有敏感值从 .env 读取，绝不硬编码。
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    APP_TITLE: str = "医院信息系统 (HIS)"
    APP_VERSION: str = "1.0.0"

    # ── Database ─────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "his_db"
    DB_USER: str = "his_user"
    DB_PASSWORD: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )

    # ── JWT ──────────────────────────────────────────────────
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # ── Dashscope (阿里云百炼) ────────────────────────────────
    DASHSCOPE_API_KEY: str
    DASHSCOPE_MODEL: str = "qwen3.7-max"

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    SESSION_CACHE_TTL: int = 1800  # 用户会话缓存：30分钟
    PATIENT_CACHE_TTL: int = 300  # 患者信息缓存：5分钟
    KB_CACHE_TTL: int = 600  # 知识库查询缓存：10分钟
    RAG_CACHE_TTL: int = 3600  # RAG 向量检索缓存：1小时

    # ── Qdrant 向量数据库 ────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "his_knowledge_base"

    # ── CORS ─────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例：全局唯一配置实例，避免重复读取 .env。"""
    return Settings()


settings = get_settings()
