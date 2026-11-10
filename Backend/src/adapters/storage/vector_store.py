"""pgvector-backed vector store implementation."""

from __future__ import annotations

from uuid import UUID
from typing import Optional, List, Dict, Any
from sqlmodel import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.adapters.storage.models import FinancialChunkRecord
from src.application.ports.outbound.vector_store import VectorStore,VectorSearchResult


def _make_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(database_url, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class PgVectorStore(VectorStore):
    """pgvector-backed implementation for financial document chunks."""

    def __init__(self, database_url: Optional[str] = None, session: Optional[AsyncSession] = None) -> None:
        self._session = session
        self._session_factory = None
        if session is None:
            if database_url is not None:
                self._session_factory = _make_session_factory(database_url)
            else:
                from src.adapters.storage.database import session_factory
                self._session_factory = session_factory()

    async def _get_session(self):
        if self._session is not None:
            return self._session
        return self._session_factory()

    async def insert(
        self,
        id: str,
        embedding: List[float],
        content: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Insert a single vector with metadata."""
        doc_id = UUID(id) if isinstance(id, str) else id
        document_id = metadata.get("document_id")
        if isinstance(document_id, str):
            document_id = UUID(document_id)

        async with (self._session if self._session else self._session_factory()) as session:
            existing = await session.get(FinancialChunkRecord, doc_id)
            ticker = metadata["ticker"]
            filing_type = metadata["filing_type"]
            fiscal_year = metadata.get("fiscal_year")
            quarter = metadata.get("quarter")
            section = metadata.get("section")
            chunk_index = metadata.get("chunk_index", 0)

            if existing is not None:
                existing.chunk_text = content
                existing.embedding = embedding
                existing.ticker = ticker
                existing.filing_type = filing_type
                existing.fiscal_year = fiscal_year
                existing.quarter = quarter
                existing.section = section
                existing.chunk_index = chunk_index
                existing.metadata_json = metadata
                if document_id is not None:
                    existing.document_id = document_id
                session.add(existing)
            else:
                session.add(
                    FinancialChunkRecord(
                        id=doc_id,
                        ticker=ticker,
                        document_id=document_id,
                        filing_type=filing_type,
                        fiscal_year=fiscal_year,
                        quarter=quarter,
                        section=section,
                        chunk_index=chunk_index,
                        chunk_text=content,
                        embedding=embedding,
                        metadata_json=metadata,
                    )
                )
            await session.commit()

    async def insert_batch(
        self,
        records: List[Dict[str, Any]],
    ) -> None:
        """Insert multiple vectors in batch."""
        async with (self._session if self._session else self._session_factory()) as session:
            for record in records:
                doc_id = UUID(record["id"]) if isinstance(record["id"], str) else record["id"]
                metadata = record["metadata"]
                document_id = metadata.get("document_id")
                if isinstance(document_id, str):
                    document_id = UUID(document_id)

                existing = await session.get(FinancialChunkRecord, doc_id)
                ticker = metadata["ticker"]
                filing_type = metadata["filing_type"]
                fiscal_year = metadata.get("fiscal_year")
                quarter = metadata.get("quarter")
                section = metadata.get("section")
                chunk_index = metadata.get("chunk_index", 0)
                content = record["content"]
                embedding = record["embedding"]

                if existing is not None:
                    existing.chunk_text = content
                    existing.embedding = embedding
                    existing.ticker = ticker
                    existing.filing_type = filing_type
                    existing.fiscal_year = fiscal_year
                    existing.quarter = quarter
                    existing.section = section
                    existing.chunk_index = chunk_index
                    existing.metadata_json = metadata
                    if document_id is not None:
                        existing.document_id = document_id
                    session.add(existing)
                else:
                    session.add(
                        FinancialChunkRecord(
                            id=doc_id,
                            ticker=ticker,
                            document_id=document_id,
                            filing_type=filing_type,
                            fiscal_year=fiscal_year,
                            quarter=quarter,
                            section=section,
                            chunk_index=chunk_index,
                            chunk_text=content,
                            embedding=embedding,
                            metadata_json=metadata,
                        )
                    )
            await session.commit()

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """Search for similar vectors using cosine similarity."""
        distance = FinancialChunkRecord.embedding.cosine_distance(query_embedding)

        async with (self._session if self._session else self._session_factory()) as session:
            stmt = select(FinancialChunkRecord, distance.label("distance"))

            if filter_metadata:
                for key, val in filter_metadata.items():
                    if hasattr(FinancialChunkRecord, key):
                        stmt = stmt.where(getattr(FinancialChunkRecord, key) == val)
                    elif key == "ticker":
                        stmt = stmt.where(FinancialChunkRecord.ticker == val)

            stmt = stmt.order_by(distance).limit(top_k)
            result = await session.execute(stmt)
            rows = result.all()

            results = []
            for chunk, dist in rows:
                dist_val = float(dist) if dist is not None else 0.0
                score = 1.0 - dist_val
                results.append(
                    VectorSearchResult(
                        id=str(chunk.id),
                        content=chunk.chunk_text,
                        metadata=chunk.metadata_json or {},
                        similarity_score=score,
                        distance=dist_val,
                    )
                )
            return results

    async def delete_by_id(self, id: str) -> None:
        """Delete a vector by ID."""
        doc_id = UUID(id) if isinstance(id, str) else id
        async with (self._session if self._session else self._session_factory()) as session:
            chunk = await session.get(FinancialChunkRecord, doc_id)
            if chunk:
                await session.delete(chunk)
                await session.commit()

    async def delete_by_metadata(self, filter_metadata: Dict[str, Any]) -> int:
        """Delete vectors matching metadata filters."""
        async with (self._session if self._session else self._session_factory()) as session:
            stmt = delete(FinancialChunkRecord)
            for key, val in filter_metadata.items():
                if hasattr(FinancialChunkRecord, key):
                    stmt = stmt.where(getattr(FinancialChunkRecord, key) == val)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount or 0

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        """Count vectors, optionally filtered by metadata."""
        async with (self._session if self._session else self._session_factory()) as session:
            stmt = select(func.count()).select_from(FinancialChunkRecord)
            if filter_metadata:
                for key, val in filter_metadata.items():
                    if hasattr(FinancialChunkRecord, key):
                        stmt = stmt.where(getattr(FinancialChunkRecord, key) == val)
            result = await session.execute(stmt)
            return result.scalar_one()

    async def upsert(
        self, doc_id: UUID, text: str, embedding: list[float], metadata: dict, document_id: Optional[UUID] = None
    ) -> None:
        """Upsert a document chunk with its embedding (compatibility wrapper for insert)."""
        await self.insert(
            id=str(doc_id),
            embedding=embedding,
            content=text,
            metadata={**metadata, "document_id": document_id} if document_id else metadata,
        )

    async def query(
        self,
        embedding: list[float],
        ticker: str,
        top_k: int = 5,
        filing_type: Optional[str] = None,
        fiscal_year: Optional[int] = None,
    ) -> list[dict]:
        """Perform vector cosine distance search filtered by ticker (compatibility wrapper for search)."""
        filters: Dict[str, Any] = {"ticker": ticker}
        if filing_type:
            filters["filing_type"] = filing_type
        if fiscal_year:
            filters["fiscal_year"] = fiscal_year
        results = await self.search(
            query_embedding=embedding,
            top_k=top_k,
            filter_metadata=filters,
        )
        return [
            {
                "id": r.id,
                "ticker": r.metadata.get("ticker", ticker),
                "filing_type": r.metadata.get("filing_type"),
                "fiscal_year": r.metadata.get("fiscal_year"),
                "quarter": r.metadata.get("quarter"),
                "section": r.metadata.get("section"),
                "chunk_text": r.content,
                "distance": r.distance,
                "score": r.similarity_score,
                "metadata": r.metadata,
            }
            for r in results
        ]
