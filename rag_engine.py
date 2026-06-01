"""
rag_engine.py — 基于 LangChain + Qdrant 的新一代 RAG 引擎

替代原有的纯手工实现（MySQL 存向量 + Python 余弦相似度），
使用 LangChain 生态的标准组件：DocumentLoader → TextSplitter → Embeddings → VectorStore。

对外通过 rag_service.py 的适配层暴露，保持与原有 API 完全兼容。
"""

from __future__ import annotations

import hashlib
import io
import json
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_qdrant import QdrantVectorStore as Qdrant
from langchain_core.documents import Document
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from ai_engine.connections import get_qdrant_client
from config import settings

# ── Dashscope Embeddings（单例） ─────────────────────────────

_embeddings: Optional[DashScopeEmbeddings] = None


def get_embeddings() -> DashScopeEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
        )
    return _embeddings


# ── 文本分块器 ─────────────────────────────────────────────


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )


# ── Collection 管理 ─────────────────────────────────────────

COLLECTION_NAME = settings.QDRANT_COLLECTION
VECTOR_SIZE = 1536  # text-embedding-v2 输出维度


def ensure_collection_exists(client: QdrantClient):
    """确保 Qdrant collection 存在，不存在则创建。"""
    collections = client.get_collections().collections
    existing = {c.name for c in collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qdrant_models.VectorParams(
                size=VECTOR_SIZE,
                distance=qdrant_models.Distance.COSINE,
            ),
        )
        # 创建 payload 索引：按 document_id 高效过滤
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="document_id",
            field_schema=qdrant_models.PayloadSchemaType.INTEGER,
        )
        logger.info(f"✅ 已创建 Qdrant collection: {COLLECTION_NAME}")
    else:
        logger.info(f"ℹ️  Qdrant collection 已存在: {COLLECTION_NAME}")


# ── 文档加载器工厂 ─────────────────────────────────────────

SUPPORTED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}


def load_document(content: bytes, filename: str) -> List[Document]:
    """根据文件扩展名选择合适的 LangChain DocumentLoader。"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

    if ext == "pdf":
        # PyPDFLoader 需要文件路径，写入临时内存文件
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            return docs
        finally:
            import os

            os.unlink(tmp_path)

    elif ext in ("docx", "doc"):
        from tempfile import NamedTemporaryFile

        suffix = ".docx" if ext == "docx" else ".doc"
        with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            loader = Docx2txtLoader(tmp_path)
            docs = loader.load()
            return docs
        finally:
            import os

            os.unlink(tmp_path)

    elif ext == "txt":
        text = content.decode("utf-8", errors="replace")
        return [Document(page_content=text, metadata={"source": filename})]

    else:
        raise ValueError(f"不支持的文件格式: .{ext}")


def _clean_text(text: str) -> str:
    """清洗文本（保留与原版兼容）。"""
    import re

    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{3,}", " ", text)
    return text.strip()


# ── RAG 引擎核心 ────────────────────────────────────────────


class RAGEngine:
    """基于 LangChain + Qdrant 的 RAG 引擎。

    职责：
    - 文档解析（LangChain DocumentLoader）
    - 文本分块（RecursiveCharacterTextSplitter）
    - 向量化（DashScopeEmbeddings）
    - 向量存储与检索（Qdrant）
    - 集合管理（自动建表/索引）
    """

    def __init__(self):
        self._client: Optional[QdrantClient] = None
        self._vector_store: Optional[Qdrant] = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = get_qdrant_client()
            ensure_collection_exists(self._client)
        return self._client

    @property
    def vector_store(self) -> Qdrant:
        if self._vector_store is None:
            self._vector_store = Qdrant(
                client=self.client,
                collection_name=COLLECTION_NAME,
                embedding=get_embeddings(),
            )
        return self._vector_store

    # ── 文档入库 ─────────────────────────────────────────

    def add_document(
        self,
        content: bytes,
        filename: str,
        document_id: int,
        document_title: str,
    ) -> int:
        """上传文档：解析 → 分块 → 向量化 → 存入 Qdrant。

        Args:
            content: 文件二进制内容
            filename: 原始文件名
            document_id: 数据库中 KnowledgeDocument.id
            document_title: 文档标题

        Returns:
            chunk_count: 分块数量
        """
        # 1. 解析
        raw_docs = load_document(content, filename)
        if not raw_docs:
            raise ValueError("文档解析后内容为空")

        # 2. 清洗
        for doc in raw_docs:
            doc.page_content = _clean_text(doc.page_content)

        full_text = "\n\n".join(d.page_content for d in raw_docs if d.page_content.strip())
        if not full_text:
            raise ValueError("文档内容清洗后为空")

        # 3. 分块
        splitter = get_text_splitter()
        chunks = splitter.split_text(full_text)

        # 4. 转为 Document 列表（带 metadata）
        docs = [
            Document(
                page_content=chunk,
                metadata={
                    "document_id": document_id,
                    "chunk_index": i,
                    "document_title": document_title,
                    "source": filename,
                },
            )
            for i, chunk in enumerate(chunks)
        ]

        # 5. 写入 Qdrant（自动向量化）
        self.vector_store.add_documents(docs)
        logger.info(
            f"📄 文档入库完成: {filename} → {len(chunks)} chunks, " f"collection={COLLECTION_NAME}"
        )

        return len(chunks)

    # ── 语义检索 ─────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """语义检索：向量化查询 → Qdrant ANN 搜索 → 返回结果。

        Args:
            query: 用户查询文本
            top_k: 返回 top-K 结果

        Returns:
            [{"content": str, "document_title": str, "score": float}, ...]
        """
        docs_with_score = self.vector_store.similarity_search_with_score(query, k=top_k)

        results = []
        for doc, score in docs_with_score:
            results.append(
                {
                    "content": doc.page_content[:500],
                    "document_title": doc.metadata.get("document_title", ""),
                    "score": round(float(score), 4),
                }
            )

        return results

    # ── 文档删除 ─────────────────────────────────────────

    def delete_document(self, document_id: int):
        """按 document_id 删除 Qdrant 中所有相关向量点。"""
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="document_id",
                            match=qdrant_models.MatchValue(value=document_id),
                        )
                    ]
                ),
            )
            logger.info(f"🗑️  已从 Qdrant 删除文档: document_id={document_id}")
        except Exception as e:
            logger.error(f"Qdrant 删除失败: {e}")

    @property
    def collection_name(self) -> str:
        """当前使用的 Qdrant collection 名称。"""
        return COLLECTION_NAME

    # ── 删除所有数据（用于重建） ──────────────────────────

    def delete_all(self):
        """清空当前 collection 的所有向量。"""
        try:
            self.client.delete_collection(COLLECTION_NAME)
            ensure_collection_exists(self.client)
            logger.info(f"🗑️  已清空 collection: {COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"清空 collection 失败: {e}")


# ── 全局单例 ────────────────────────────────────────────────

_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine
