"""In-memory RAG adapter (keyword matching) — mirrors lemura/src/rag/InMemoryRAGAdapter.ts"""
from __future__ import annotations
import uuid
from pylemura.types.rag import (
    IRAGAdapter,
    RAGDocument,
    RAGIngestRequest,
    RAGIngestResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGQueryResult,
)


class InMemoryRAGAdapter(IRAGAdapter):
    def __init__(self) -> None:
        self._namespaces: dict[str, list[RAGDocument]] = {}

    async def ingest(self, request: RAGIngestRequest) -> RAGIngestResponse:
        ns = self._namespaces.setdefault(request.namespace, [])
        ids: list[str] = []
        for doc in request.documents:
            if not doc.id:
                doc.id = str(uuid.uuid4())
            # Replace if id already exists
            existing = next((i for i, d in enumerate(ns) if d.id == doc.id), None)
            if existing is not None:
                ns[existing] = doc
            else:
                ns.append(doc)
            ids.append(doc.id)
        return RAGIngestResponse(ingested=len(ids), ids=ids)

    async def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        ns = self._namespaces.get(request.namespace, [])
        if not ns:
            return RAGQueryResponse(results=[], namespace=request.namespace)

        query_terms = set(request.query.lower().split())
        scored: list[RAGQueryResult] = []

        for doc in ns:
            content_words = set(doc.content.lower().split())
            if not query_terms:
                score = 0.0
            else:
                overlap = query_terms & content_words
                score = len(overlap) / len(query_terms)

            if score >= request.min_score:
                scored.append(RAGQueryResult(document=doc, score=score))

        scored.sort(key=lambda r: r.score, reverse=True)
        return RAGQueryResponse(
            results=scored[: request.top_k],
            namespace=request.namespace,
        )

    async def delete(self, ids: list[str]) -> None:
        id_set = set(ids)
        for ns in self._namespaces.values():
            to_remove = [d for d in ns if d.id in id_set]
            for doc in to_remove:
                ns.remove(doc)

    async def health_check(self) -> bool:
        return True
