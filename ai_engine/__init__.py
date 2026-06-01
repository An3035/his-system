"""
ai_engine — AI 引擎包
基于 LangChain + LangGraph + Qdrant + Redis 的智能多 Agent 系统

架构：
  Router Agent → 路由用户请求到专业 Agent
    ├── Consultant Agent  → 日常健康咨询
    ├── Medical Agent     → 诊疗/处方/患者信息（可调用 Tool Agent）
    └── Science Agent     → 健康科普/医疗政策（可调用 RAG）

当 Medical/Science Agent 需要 HIS 数据或知识检索时，通过 Tool Agent 执行具体工具函数。

对外接口保持与原有 ai_service.py 完全兼容。
"""

from .connections import get_qdrant_client, get_connection_manager

__all__ = ["get_qdrant_client", "get_connection_manager"]
