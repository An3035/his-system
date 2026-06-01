"""
redis_cache.py — Redis 缓存管理器
提供会话缓存、热点数据缓存、缓存防护
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
from typing import Any, Optional

import redis.asyncio as aioredis
from loguru import logger

from config import settings


class CacheManager:
    """Redis 缓存管理器（异步）"""

    def __init__(self, redis_url: str):
        self._redis: Optional[aioredis.Redis] = None
        self._redis_url = redis_url
        self._lock: dict[str, asyncio.Lock] = {}

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self._redis_url,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=True,
            )
        return self._redis

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _ttl_jitter(self, base_ttl: int) -> int:
        """添加随机抖动避免缓存雪崩（±20%）。"""
        jitter = int(base_ttl * 0.2 * (random.random() * 2 - 1))
        return max(60, base_ttl + jitter)

    async def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._lock:
            self._lock[key] = asyncio.Lock()
        if len(self._lock) > 1000:
            self._lock.clear()
        return self._lock[key]

    # ── 用户会话缓存 ─────────────────────────────────────────

    async def get_user_session(self, user_id: int) -> Optional[dict]:
        r = await self._get_redis()
        try:
            data = await r.get(f"session:user:{user_id}")
            return json.loads(data) if data else None
        except Exception:
            return None

    async def set_user_session(self, user_id: int, data: dict, ttl: int | None = None):
        r = await self._get_redis()
        ttl = ttl or self._ttl_jitter(settings.SESSION_CACHE_TTL)
        try:
            await r.setex(
                f"session:user:{user_id}",
                ttl,
                json.dumps(data, ensure_ascii=False),
            )
        except Exception as e:
            logger.warning(f"Redis set_user_session failed: {e}")

    # ── 患者信息缓存 ─────────────────────────────────────────

    async def get_patient_cache(self, patient_id: int) -> Optional[dict]:
        r = await self._get_redis()
        try:
            data = await r.get(f"patient:{patient_id}")
            return json.loads(data) if data else None
        except Exception:
            return None

    async def set_patient_cache(self, patient_id: int, data: dict, ttl: int | None = None):
        r = await self._get_redis()
        ttl = ttl or self._ttl_jitter(settings.PATIENT_CACHE_TTL)
        try:
            await r.setex(
                f"patient:{patient_id}",
                ttl,
                json.dumps(data, ensure_ascii=False, default=str),
            )
        except Exception as e:
            logger.warning(f"Redis set_patient_cache failed: {e}")

    async def invalidate_patient_cache(self, patient_id: int):
        r = await self._get_redis()
        try:
            await r.delete(f"patient:{patient_id}")
        except Exception:
            pass

    # ── 知识库查询缓存 ───────────────────────────────────────

    async def get_kb_cache(self, query: str) -> Optional[list]:
        r = await self._get_redis()
        key = f"kb:search:{self._hash(query)}"
        try:
            data = await r.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    async def set_kb_cache(self, query: str, results: list, ttl: int | None = None):
        r = await self._get_redis()
        ttl = ttl or self._ttl_jitter(settings.KB_CACHE_TTL)
        key = f"kb:search:{self._hash(query)}"
        try:
            await r.setex(key, ttl, json.dumps(results, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Redis set_kb_cache failed: {e}")

    # ── 药物相互作用缓存 ─────────────────────────────────────

    async def get_drug_interaction_cache(self, drug_names: str) -> Optional[str]:
        r = await self._get_redis()
        key = f"drug:int:{self._hash(drug_names)}"
        try:
            return await r.get(key)
        except Exception:
            return None

    async def set_drug_interaction_cache(self, drug_names: str, result: str, ttl: int = 3600):
        r = await self._get_redis()
        key = f"drug:int:{self._hash(drug_names)}"
        try:
            await r.setex(key, ttl, result)
        except Exception as e:
            logger.warning(f"Redis set_drug_interaction_cache failed: {e}")

    # ── 缓存击穿防护：互斥锁 ─────────────────────────────────

    async def get_or_set(
        self,
        cache_key: str,
        fetcher,  # async callable
        ttl: int = 300,
        lock_ttl: int = 10,
    ) -> Any:
        """防击穿：拿不到缓存时加锁等待，避免大量请求同时穿透到DB。"""
        r = await self._get_redis()

        # 先读缓存
        try:
            cached = await r.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

        # 互斥锁
        lock_key = f"{cache_key}:lock"
        lock = await self._get_lock(lock_key)
        async with lock:
            # 双重检查
            try:
                cached = await r.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

            # 获取数据
            data = await fetcher()
            try:
                await r.setex(cache_key, self._ttl_jitter(ttl), json.dumps(data, ensure_ascii=False, default=str))
            except Exception:
                pass
            return data

    # ── 缓存穿透防护：空值缓存 ─────────────────────────────────

    async def get_with_null_guard(self, key: str, fetcher, ttl: int = 300) -> Any:
        """缓存空值，防止穿透。"""
        r = await self._get_redis()
        try:
            cached = await r.get(key)
            if cached is not None:
                return json.loads(cached) if cached != "__NULL__" else None
        except Exception:
            pass

        data = await fetcher()
        try:
            value = "__NULL__" if data is None else json.dumps(data, ensure_ascii=False, default=str)
            await r.setex(key, self._ttl_jitter(ttl) if data else 60, value)
        except Exception:
            pass
        return data

    # ── RAG 向量检索缓存（1小时 TTL） ─────────────────────────

    async def get_rag_cache(self, query: str) -> Optional[list]:
        """获取 RAG 检索缓存。键格式: rag:query:{sha256(query)[:16]}"""
        r = await self._get_redis()
        key = f"rag:query:{self._hash(query)}"
        try:
            data = await r.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    async def set_rag_cache(
        self, query: str, results: list, ttl: int | None = None
    ):
        """设置 RAG 检索缓存，默认 1 小时。"""
        r = await self._get_redis()
        ttl = ttl or self._ttl_jitter(settings.RAG_CACHE_TTL)
        key = f"rag:query:{self._hash(query)}"
        try:
            await r.setex(key, ttl, json.dumps(results, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Redis set_rag_cache failed: {e}")

    async def invalidate_rag_cache(self):
        """知识库更新时清除所有 RAG 缓存。"""
        r = await self._get_redis()
        try:
            keys = []
            async for key in r.scan_iter(match="rag:query:*", count=200):
                keys.append(key)
            if keys:
                await r.delete(*keys)
                logger.info(f"🧹 已清除 {len(keys)} 条 RAG 缓存")
        except Exception as e:
            logger.warning(f"Redis invalidate_rag_cache failed: {e}")

    # ── 通用失效 ─────────────────────────────────────────────

    async def invalidate(self, pattern: str):
        """按模式删除缓存键。"""
        r = await self._get_redis()
        try:
            keys = []
            async for key in r.scan_iter(match=f"*{pattern}*", count=100):
                keys.append(key)
                if len(keys) >= 100:
                    break
            if keys:
                await r.delete(*keys)
        except Exception:
            pass

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None


# 全局单例
_cache_manager: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(settings.REDIS_URL)
    return _cache_manager
