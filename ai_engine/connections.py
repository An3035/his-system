"""
connections.py — Qdrant + Redis 连接管理器
统一管理外部基础设施连接，提供单例访问。
"""

from __future__ import annotations

from typing import Optional

from loguru import logger
from qdrant_client import QdrantClient

from config import settings


class ConnectionManager:
    """Qdrant + Redis 连接管理单例。

    特性：
    - 延迟初始化（首次使用时才建立连接）
    - 连接健康检查
    - 优雅关闭
    """

    def __init__(self):
        self._qdrant: Optional[QdrantClient] = None
        self._qdrant_url: str = (
            f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        )

    # ── Qdrant ─────────────────────────────────────────────────

    def get_qdrant(self) -> QdrantClient:
        """获取 Qdrant 客户端（延迟初始化）。"""
        if self._qdrant is None:
            try:
                self._qdrant = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    timeout=30,
                )
                # 验证连接
                self._qdrant.get_collections()
                logger.info(
                    f"✅ Qdrant 已连接 {settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
                )
            except Exception as e:
                logger.error(f"❌ Qdrant 连接失败: {e}")
                raise
        return self._qdrant

    async def health_check_qdrant(self) -> bool:
        """检查 Qdrant 健康状态。"""
        try:
            client = self.get_qdrant()
            client.get_collections()
            return True
        except Exception:
            return False

    async def close_qdrant(self):
        """关闭 Qdrant 连接。"""
        if self._qdrant is not None:
            self._qdrant.close()
            self._qdrant = None
            logger.info("Qdrant 连接已关闭")

    @property
    def qdrant_url(self) -> str:
        return self._qdrant_url


# ── 全局单例 ────────────────────────────────────────────────

_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


def get_qdrant_client() -> QdrantClient:
    """便捷函数：直接获取 Qdrant 客户端。"""
    return get_connection_manager().get_qdrant()
