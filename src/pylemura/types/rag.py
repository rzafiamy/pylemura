"""RAG interfaces — mirrors lemura/src/types/rag.ts"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RAGDocument:
    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGIngestRequest:
    documents: list[RAGDocument]
    namespace: str = "default"


@dataclass
class RAGIngestResponse:
    ingested: int
    ids: list[str]


@dataclass
class RAGQueryRequest:
    query: str
    namespace: str = "default"
    top_k: int = 5
    min_score: float = 0.0
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGQueryResult:
    document: RAGDocument
    score: float


@dataclass
class RAGQueryResponse:
    results: list[RAGQueryResult]
    namespace: str = "default"


class IRAGAdapter(ABC):
    @abstractmethod
    async def ingest(self, request: RAGIngestRequest) -> RAGIngestResponse: ...

    @abstractmethod
    async def query(self, request: RAGQueryRequest) -> RAGQueryResponse: ...

    async def delete(self, ids: list[str]) -> None:
        raise NotImplementedError

    async def health_check(self) -> bool:
        return True
