from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Any


@dataclass
class KnowledgeChunk:
    chunk_id: str
    modality: str
    text: str
    metadata: dict[str, Any]


class MultiModalIngestor:
    """Offline runnable multimodal ingestion with clear OCR stub boundary."""

    def ingest(
        self,
        *,
        text: str | None = None,
        csv_text: str | None = None,
        markdown_table: str | None = None,
        image_bytes: bytes | None = None,
        ocr_fn: Any | None = None,
    ) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []

        if text:
            chunks.extend(self._from_text(text))
        if csv_text:
            chunks.extend(self._from_csv(csv_text))
        if markdown_table:
            chunks.extend(self._from_markdown_table(markdown_table))
        if image_bytes is not None:
            chunks.extend(self._from_image(image_bytes, ocr_fn=ocr_fn))

        return chunks

    def _from_text(self, text: str) -> list[KnowledgeChunk]:
        parts = [p.strip() for p in text.split("\n") if p.strip()]
        return [
            KnowledgeChunk(chunk_id=f"text_{idx}", modality="text", text=part, metadata={"line": idx})
            for idx, part in enumerate(parts)
        ]

    def _from_csv(self, csv_text: str) -> list[KnowledgeChunk]:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        rows = list(reader)
        chunks: list[KnowledgeChunk] = []
        for idx, row in enumerate(rows):
            serialized = "; ".join(f"{k}={v}" for k, v in row.items())
            chunks.append(KnowledgeChunk(chunk_id=f"csv_{idx}", modality="table", text=serialized, metadata={"source": "csv"}))
        return chunks

    def _from_markdown_table(self, markdown: str) -> list[KnowledgeChunk]:
        lines = [ln.strip() for ln in markdown.strip().splitlines() if ln.strip()]
        if len(lines) < 2:
            return []
        header = [h.strip() for h in lines[0].strip("|").split("|")]
        chunks: list[KnowledgeChunk] = []
        for idx, line in enumerate(lines[2:]):
            cells = [c.strip() for c in line.strip("|").split("|")]
            row = dict(zip(header, cells))
            serialized = "; ".join(f"{k}={v}" for k, v in row.items())
            chunks.append(KnowledgeChunk(chunk_id=f"mdtbl_{idx}", modality="table", text=serialized, metadata={"source": "markdown_table"}))
        return chunks

    def _from_image(self, image_bytes: bytes, ocr_fn: Any | None = None) -> list[KnowledgeChunk]:
        # Replaceable OCR boundary:
        # - If `ocr_fn` is provided, call it with image bytes and expect str output.
        # - Otherwise run deterministic stub text so the pipeline is executable offline.
        if ocr_fn is None:
            extracted = f"[OCR_STUB] image_size={len(image_bytes)} bytes"
        else:
            extracted = str(ocr_fn(image_bytes))

        return [KnowledgeChunk(chunk_id="img_0", modality="image", text=extracted, metadata={"ocr": "stub" if ocr_fn is None else "external"})]
