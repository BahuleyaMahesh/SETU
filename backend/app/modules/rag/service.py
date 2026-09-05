from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from ...db.models.rag_document import RAGDocument
from ...db.models.rag_chunk import RAGChunk
from .schemas import RAGQuery, RAGResponse, DocumentIngestionRequest
from .providers.embeddings import GeminiEmbeddingProvider


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RAGService:
    """Service for RAG (Retrieval-Augmented Generation) operations"""

    def __init__(self, db):
        self.db = db
        self.embedding_provider = GeminiEmbeddingProvider()

    async def ingest_document(
        self,
        request: DocumentIngestionRequest,
    ) -> RAGDocument:
        """Ingest a document into the RAG system"""
        # Create document record
        doc = RAGDocument(
            source_type=request.source_type,
            source_id=request.source_id,
            title=request.title,
            content=request.content,
            source_url=request.source_url,
            published_date=request.published_date,
            is_active=True,
            alert_metadata={
                "tags": request.tags or [],
                "language": request.language or "en",
            },
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        # Create chunks (with embeddings when a real embedding provider is configured)
        chunks = self._chunk_text(request.content)
        for i, chunk_content in enumerate(chunks):
            embedding = None
            if self.embedding_provider.available():
                embedding = await self.embedding_provider.embed(chunk_content)

            chunk = RAGChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk_content,
                embedding=embedding,
                token_count=len(chunk_content.split()),
                chunk_alert_metadata={
                    "offset": i * 1000,
                    "length": len(chunk_content),
                },
            )
            self.db.add(chunk)

        await self.db.commit()

        return doc

    async def query_rag(
        self,
        query: str,
        user_role: str,
        top_k: int = 5,
    ) -> RAGResponse:
        """Query the RAG system"""
        # Get relevant chunks
        chunks = await self._retrieve_chunks(query, top_k)

        if not chunks:
            return RAGResponse(
                response="I couldn't find any relevant information.",
                sources=[],
                confidence=0.0,
            )

        # Format context from chunks
        context = "\n\n".join([c.content for c in chunks])

        # Get source metadata
        sources = [
            {
                "document_id": str(c.document_id),
                "title": c.document.title if hasattr(c, "document") else "Unknown",
                "source_type": c.document.source_type if hasattr(c, "document") else "unknown",
                "relevance": 0.8 - (i * 0.1),
            }
            for i, c in enumerate(chunks[:top_k])
        ]

        return RAGResponse(
            response=context,
            sources=sources,
            confidence=0.8,
        )

    async def _retrieve_chunks(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[RAGChunk]:
        """Retrieve relevant chunks for a query.

        Uses Gemini embedding cosine-similarity when a chunk has a stored
        embedding; otherwise falls back to simple keyword overlap so
        retrieval still works without an API key.
        """
        from sqlalchemy import select
        stmt = select(RAGChunk)
        result = await self.db.execute(stmt)
        chunks = result.scalars().all()

        query_embedding = None
        if self.embedding_provider.available():
            query_embedding = await self.embedding_provider.embed(query)

        query_terms = query.lower().split()
        scored_chunks = []
        for chunk in chunks:
            if query_embedding is not None and chunk.embedding:
                score = _cosine_similarity(query_embedding, chunk.embedding)
            else:
                chunk_terms = chunk.content.lower().split()
                score = sum(1 for term in query_terms if term in chunk_terms)
            if score > 0:
                scored_chunks.append((chunk, score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in scored_chunks[:top_k]]

    async def get_document(self, document_id: str) -> Optional[RAGDocument]:
        """Get a RAG document by ID"""
        from sqlalchemy import select
        stmt = select(RAGDocument).where(RAGDocument.id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_document_chunks(
        self,
        document_id: str,
    ) -> List[RAGChunk]:
        """Get all chunks for a document"""
        from sqlalchemy import select
        stmt = select(RAGChunk).where(RAGChunk.document_id == document_id).order_by(RAGChunk.chunk_index)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_available_documents(
        self,
        source_type: str = None,
    ) -> List[RAGDocument]:
        """Get available RAG documents"""
        from sqlalchemy import select
        stmt = select(RAGDocument).where(RAGDocument.is_active == True)
        if source_type:
            stmt = stmt.where(RAGDocument.source_type == source_type)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            if len(" ".join(current_chunk + [word])) > chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
            else:
                current_chunk.append(word)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


def get_rag_service(db):
    """Get RAG service instance"""
    return RAGService(db)
