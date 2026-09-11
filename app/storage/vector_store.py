from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

from app.core.exceptions import StorageError
from app.ingestion.types import Chunk


@dataclass(slots=True)
class VectorHit:
    chunk_id: str
    text: str
    distance: float
    metadata: dict[str, Any]


class VectorStoreAdapter:
    def __init__(self, path: Path, collection_name: str):
        path.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise StorageError("Chunk and embedding counts do not match")
        try:
            self.collection.add(
                ids=[chunk.chunk_id for chunk in chunks],
                embeddings=embeddings,
                documents=[chunk.text for chunk in chunks],
                metadatas=[chunk.chroma_metadata() for chunk in chunks],
            )
        except Exception as exc:
            raise StorageError("Failed to write vectors") from exc

    def query(self, embedding: list[float], n_results: int) -> list[VectorHit]:
        try:
            result = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise StorageError("Vector query failed") from exc

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        hits: list[VectorHit] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            hits.append(
                VectorHit(
                    chunk_id=chunk_id,
                    text=text or "",
                    distance=float(distance),
                    metadata=metadata or {},
                )
            )
        return hits

    def delete_by_document(self, document_id: str) -> None:
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as exc:
            raise StorageError("Failed to delete document vectors") from exc

    def count_by_document(self, document_id: str) -> int:
        try:
            result = self.collection.get(where={"document_id": document_id}, include=[])
            return len(result.get("ids", []))
        except Exception as exc:
            raise StorageError("Failed to verify document vectors") from exc

    def ping(self) -> bool:
        self.collection.count()
        return True
