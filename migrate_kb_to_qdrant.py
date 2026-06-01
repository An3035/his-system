#!/usr/bin/env python3
"""
migrate_kb_to_qdrant.py — 知识库数据迁移脚本
将 MySQL KnowledgeChunk 表中的向量数据迁移到 Qdrant 向量数据库。

用法：
    python migrate_kb_to_qdrant.py          # 正常迁移
    python migrate_kb_to_qdrant.py --force  # 清空 Qdrant collection 后重新导入
    python migrate_kb_to_qdrant.py --dry-run # 仅扫描，不实际写入

前置条件：
    1. Qdrant 服务已启动（docker-compose up -d）
    2. MySQL 中有 KnowledgeChunk 数据
    3. Dashscope API Key 已配置（.env）
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ── 项目初始化 ─────────────────────────────────────────────

# 需要在项目根目录运行
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def count_source(db: AsyncSession) -> int:
    """统计 MySQL 中有 embedding 的数据量。"""
    from models import KnowledgeChunk

    result = await db.execute(
        select(KnowledgeChunk.id)
        .where(KnowledgeChunk.embedding.isnot(None))
    )
    return len(result.all())


async def migrate(dry_run: bool = False, force: bool = False):
    """执行迁移。"""
    from database import AsyncSessionLocal
    from models import KnowledgeChunk, KnowledgeDocument
    from rag_engine import get_rag_engine

    engine = get_rag_engine()

    if force:
        print("🧹 --force: 清空 Qdrant collection...")
        engine.delete_all()

    print("🔌 连接 MySQL...")
    async with AsyncSessionLocal() as db:
        # 获取所有活跃文档
        doc_result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.is_active == True,
                KnowledgeDocument.chunk_count > 0,
            )
        )
        documents = doc_result.scalars().all()
        print(f"📄 找到 {len(documents)} 个活跃文档")

        # 获取 chunks
        chunk_result = await db.execute(
            select(KnowledgeChunk)
            .join(
                KnowledgeDocument,
                KnowledgeChunk.document_id == KnowledgeDocument.id,
            )
            .where(
                KnowledgeDocument.is_active == True,
                KnowledgeChunk.content != "",
            )
            .order_by(KnowledgeChunk.document_id, KnowledgeChunk.chunk_index)
        )
        chunks = chunk_result.scalars().all()
        print(f"🧩 找到 {len(chunks)} 个知识块")

        if not chunks:
            print("⚠️  没有需要迁移的数据")
            return

        if dry_run:
            print("\n🔍 Dry Run 模式 — 仅扫描，不写入 Qdrant")
            print(f"   活跃文档数: {len(documents)}")
            print(f"   知识块数:   {len(chunks)}")
            print(f"   文档列表:")
            for doc in documents:
                print(f"     [{doc.id}] {doc.title} ({doc.chunk_count} chunks)")
            print("\n✅ Dry run 完成，未写入任何数据")
            return

        # 按文档分组导入
        total = 0
        for doc in documents:
            doc_chunks = [c for c in chunks if c.document_id == doc.id]
            if not doc_chunks:
                continue

            # 构建 Document 列表
            from langchain_core.documents import Document as LCDocument

            lc_docs = []
            for i, chunk in enumerate(doc_chunks):
                lc_docs.append(
                    LCDocument(
                        page_content=chunk.content,
                        metadata={
                            "document_id": doc.id,
                            "chunk_index": i,
                            "document_title": doc.title or doc.filename,
                            "source": doc.filename,
                        },
                    )
                )

            # 写入 Qdrant
            try:
                from langchain_core.documents import Document as LCDocument
                lc_docs = [
                    LCDocument(
                        page_content=chunk.content,
                        metadata={
                            "document_id": doc.id,
                            "chunk_index": i,
                            "document_title": doc.title or doc.filename,
                            "source": doc.filename,
                        },
                    )
                    for i, chunk in enumerate(doc_chunks)
                ]
                engine.vector_store.add_documents(lc_docs)
                total += len(lc_docs)
                print(f"  ✅ [{doc.id}] {doc.title}: {len(lc_docs)} chunks 已导入")
            except Exception as e:
                print(f"  ❌ [{doc.id}] {doc.title} 导入失败: {e}")

        print(f"\n🎉 迁移完成！共导入 {total} 个知识块到 Qdrant collection '{engine.collection_name}'")

        # 验证
        collection_info = engine.client.get_collection(engine.collection_name)
        print(f"📊 Qdrant collection 统计:")
        print(f"   向量总数: {collection_info.points_count}")


async def main():
    parser = argparse.ArgumentParser(
        description="迁移 MySQL KnowledgeChunk 数据到 Qdrant 向量数据库"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅扫描不写入",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制清空 Qdrant collection 后重新导入",
    )
    args = parser.parse_args()

    print(f"╔══════════════════════════════════════════╗")
    print(f"║  知识库数据迁移：MySQL → Qdrant          ║")
    print(f"║  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}        ║")
    print(f"╚══════════════════════════════════════════╝")
    print()

    try:
        await migrate(dry_run=args.dry_run, force=args.force)
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
