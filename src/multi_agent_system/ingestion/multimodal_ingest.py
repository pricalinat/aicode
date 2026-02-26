"""Multimodal Ingestion with source spans, confidence, and document parsing.

This module provides comprehensive multimodal ingestion capabilities including:
- Text parsing with line/paragraph spans
- Table parsing (CSV, Markdown)
- Image OCR with replaceable adapter
- PDF document parsing with page-level spans
- Unified KnowledgeChunk with source spans and confidence scores
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class SourceSpan:
    """Represents a span of content in the source document."""
    start_offset: int = 0
    end_offset: int = 0
    line_start: int = 0
    line_end: int = 0
    page: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "page": self.page,
        }


@dataclass
class KnowledgeChunk:
    """A chunk of knowledge with source tracking and confidence."""
    chunk_id: str
    modality: str  # text, table, image, document
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_span: SourceSpan | None = None
    confidence: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "modality": self.modality,
            "text": self.text,
            "metadata": self.metadata,
            "source_span": self.source_span.to_dict() if self.source_span else None,
            "confidence": self.confidence,
        }


# Type alias for OCR function
OcrFunction = Callable[[bytes], str]
# Type alias for PDF parsing function
PdfParserFunction = Callable[[bytes], list[dict[str, Any]]]


class MultiModalIngestor:
    """Offline runnable multimodal ingestion with clear adapter boundaries.

    Supports:
    - Text with line spans
    - CSV/Markdown tables
    - Image OCR (replaceable adapter)
    - PDF documents (replaceable adapter)
    """

    def __init__(
        self,
        ocr_fn: OcrFunction | None = None,
        pdf_parser_fn: PdfParserFunction | None = None,
    ):
        """Initialize with optional adapters.

        Args:
            ocr_fn: Optional OCR function that takes bytes and returns text
            pdf_parser_fn: Optional PDF parser function that takes bytes
                          and returns list of page dicts with 'text' and 'page_num'
        """
        self._ocr_fn = ocr_fn
        self._pdf_parser_fn = pdf_parser_fn

    def ingest(
        self,
        *,
        text: str | None = None,
        csv_text: str | None = None,
        markdown_table: str | None = None,
        image_bytes: bytes | None = None,
        pdf_bytes: bytes | None = None,
        ocr_fn: OcrFunction | None = None,
        pdf_parser_fn: PdfParserFunction | None = None,
    ) -> list[KnowledgeChunk]:
        """Ingest content from various modalities.

        Args:
            text: Plain text content
            csv_text: CSV formatted text
            markdown_table: Markdown table text
            image_bytes: Image bytes for OCR
            pdf_bytes: PDF document bytes
            ocr_fn: Override OCR function for this call
            pdf_parser_fn: Override PDF parser for this call

        Returns:
            List of KnowledgeChunk with source spans and confidence
        """
        chunks: list[KnowledgeChunk] = []

        # Use instance adapters if not overridden
        effective_ocr_fn = ocr_fn or self._ocr_fn
        effective_pdf_fn = pdf_parser_fn or self._pdf_parser_fn

        if text:
            chunks.extend(self._from_text(text))
        if csv_text:
            chunks.extend(self._from_csv(csv_text))
        if markdown_table:
            chunks.extend(self._from_markdown_table(markdown_table))
        if image_bytes is not None:
            chunks.extend(self._from_image(image_bytes, ocr_fn=effective_ocr_fn))
        if pdf_bytes is not None:
            chunks.extend(self._from_pdf(pdf_bytes, parser_fn=effective_pdf_fn))

        return chunks

    def _from_text(self, text: str) -> list[KnowledgeChunk]:
        """Parse text with line-level spans."""
        chunks: list[KnowledgeChunk] = []
        lines = text.split("\n")
        current_offset = 0

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                current_offset += len("\n")
                continue

            line_start = current_offset
            line_end = current_offset + len(line)

            span = SourceSpan(
                start_offset=line_start,
                end_offset=line_end,
                line_start=idx,
                line_end=idx,
                page=None,
            )

            # Calculate confidence based on content quality
            confidence = self._calculate_text_confidence(line)

            chunks.append(KnowledgeChunk(
                chunk_id=f"text_{idx}",
                modality="text",
                text=line,
                metadata={"line": idx, "source": "text"},
                source_span=span,
                confidence=confidence,
            ))

            current_offset = line_end + len("\n")

        return chunks

    def _calculate_text_confidence(self, text: str) -> float:
        """Calculate confidence score for text chunk."""
        # Base confidence
        confidence = 0.8

        # Higher confidence for well-formed sentences
        if re.match(r'^[A-Z][^.!?]*[.!?]$', text):
            confidence += 0.1

        # Higher confidence for longer content
        if len(text) > 50:
            confidence += 0.05

        # Lower confidence for short fragments
        if len(text) < 10:
            confidence -= 0.1

        return max(0.1, min(1.0, confidence))

    def _from_csv(self, csv_text: str) -> list[KnowledgeChunk]:
        """Parse CSV with row-level spans."""
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        rows = list(reader)

        if not rows:
            return []

        headers = rows[0].keys() if rows else []

        chunks: list[KnowledgeChunk] = []
        current_offset = 0

        for idx, row in enumerate(rows):
            # Calculate span for this row
            serialized = "; ".join(f"{k}={v}" for k, v in row.items())
            row_start = current_offset
            row_end = current_offset + len(serialized)

            span = SourceSpan(
                start_offset=row_start,
                end_offset=row_end,
                line_start=idx,
                line_end=idx,
                page=None,
            )

            chunks.append(KnowledgeChunk(
                chunk_id=f"csv_{idx}",
                modality="table",
                text=serialized,
                metadata={
                    "source": "csv",
                    "row": idx,
                    "headers": list(headers),
                    "columns": len(row),
                },
                source_span=span,
                confidence=0.95,  # CSV is structured, high confidence
            ))

            current_offset = row_end + 1

        return chunks

    def _from_markdown_table(self, markdown: str) -> list[KnowledgeChunk]:
        """Parse Markdown table with cell-level spans."""
        lines = [ln.strip() for ln in markdown.strip().splitlines() if ln.strip()]

        if len(lines) < 2:
            return []

        # Parse header
        header = [h.strip() for h in lines[0].strip("|").split("|")]

        # Skip separator line (index 1)
        chunks: list[KnowledgeChunk] = []
        current_offset = 0

        for idx, line in enumerate(lines[2:], start=2):
            cells = [c.strip() for c in line.strip("|").split("|")]

            if len(cells) != len(header):
                continue  # Skip malformed rows

            row_dict = dict(zip(header, cells))
            serialized = "; ".join(f"{k}={v}" for k, v in row_dict.items())

            row_start = current_offset
            row_end = current_offset + len(serialized)

            span = SourceSpan(
                start_offset=row_start,
                end_offset=row_end,
                line_start=idx,
                line_end=idx,
                page=None,
            )

            chunks.append(KnowledgeChunk(
                chunk_id=f"mdtbl_{idx - 2}",
                modality="table",
                text=serialized,
                metadata={
                    "source": "markdown_table",
                    "row": idx - 2,
                    "headers": header,
                    "columns": len(cells),
                },
                source_span=span,
                confidence=0.9,  # Markdown tables are well-formed
            ))

            current_offset = row_end + 1

        return chunks

    def _from_image(
        self,
        image_bytes: bytes,
        ocr_fn: OcrFunction | None = None,
    ) -> list[KnowledgeChunk]:
        """Extract text from image using OCR.

        Args:
            image_bytes: Raw image bytes
            ocr_fn: Optional OCR function override

        Returns:
            List containing extracted text chunk
        """
        effective_ocr_fn = ocr_fn or self._ocr_fn

        if effective_ocr_fn is None:
            # Use stub for offline execution
            extracted = f"[OCR_STUB] image_size={len(image_bytes)} bytes"
            confidence = 0.3  # Low confidence for stub
            ocr_status = "stub"
        else:
            try:
                extracted = str(effective_ocr_fn(image_bytes))
                confidence = 0.85  # Higher confidence for real OCR
                ocr_status = "external"
            except Exception as e:
                extracted = f"[OCR_ERROR] {str(e)}"
                confidence = 0.1
                ocr_status = "error"

        return [KnowledgeChunk(
            chunk_id="img_0",
            modality="image",
            text=extracted,
            metadata={
                "ocr": ocr_status,
                "image_size_bytes": len(image_bytes),
            },
            source_span=SourceSpan(
                start_offset=0,
                end_offset=len(extracted),
                line_start=0,
                line_end=0,
                page=None,
            ),
            confidence=confidence,
        )]

    def _from_pdf(
        self,
        pdf_bytes: bytes,
        parser_fn: PdfParserFunction | None = None,
    ) -> list[KnowledgeChunk]:
        """Extract text from PDF document.

        Args:
            pdf_bytes: Raw PDF bytes
            parser_fn: Optional PDF parser function override

        Returns:
            List of text chunks with page-level spans
        """
        effective_parser_fn = parser_fn or self._pdf_parser_fn

        if effective_parser_fn is None:
            # Use stub for offline execution
            stub_text = f"[PDF_STUB] document_size={len(pdf_bytes)} bytes"
            return [KnowledgeChunk(
                chunk_id="pdf_0",
                modality="document",
                text=stub_text,
                metadata={
                    "pdf": "stub",
                    "document_size_bytes": len(pdf_bytes),
                    "pages": 1,
                },
                source_span=SourceSpan(
                    start_offset=0,
                    end_offset=len(stub_text),
                    line_start=0,
                    line_end=0,
                    page=1,
                ),
                confidence=0.3,
            )]

        # Use provided parser
        try:
            pages = effective_parser_fn(pdf_bytes)
        except Exception as e:
            return [KnowledgeChunk(
                chunk_id="pdf_error",
                modality="document",
                text=f"[PDF_PARSE_ERROR] {str(e)}",
                metadata={"pdf": "error", "error": str(e)},
                confidence=0.1,
            )]

        chunks: list[KnowledgeChunk] = []
        global_offset = 0

        for page_data in pages:
            page_num = page_data.get("page_num", 1)
            text = page_data.get("text", "")

            if not text:
                continue

            # Split into paragraphs/blocks
            paragraphs = self._split_into_paragraphs(text)

            for para_idx, para in enumerate(paragraphs):
                if not para.strip():
                    continue

                para_start = global_offset
                para_end = global_offset + len(para)

                span = SourceSpan(
                    start_offset=para_start,
                    end_offset=para_end,
                    line_start=0,
                    line_end=0,
                    page=page_num,
                )

                chunks.append(KnowledgeChunk(
                    chunk_id=f"pdf_p{page_num}_para{para_idx}",
                    modality="document",
                    text=para.strip(),
                    metadata={
                        "pdf": "parsed",
                        "page": page_num,
                        "paragraph": para_idx,
                    },
                    source_span=span,
                    confidence=0.85,  # Good confidence for parsed PDF
                ))

                global_offset = para_end + 1

        return chunks

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs."""
        # Split on double newlines or single newlines with indentation
        paragraphs = re.split(r'\n\s*\n|\n(?=\s)', text)
        return [p.strip() for p in paragraphs if p.strip()]


class DocumentChunker:
    """Advanced document chunking with configurable strategies."""

    @staticmethod
    def chunk_by_size(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> list[KnowledgeChunk]:
        """Chunk text by size with optional overlap."""
        chunks: list[KnowledgeChunk] = []
        start = 0
        idx = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Try to break at word boundary
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space

            chunk_text = text[start:end]

            chunks.append(KnowledgeChunk(
                chunk_id=f"size_{idx}",
                modality="text",
                text=chunk_text,
                metadata={"strategy": "size", "chunk_size": chunk_size, "overlap": overlap},
                source_span=SourceSpan(
                    start_offset=start,
                    end_offset=end,
                    line_start=0,
                    line_end=0,
                    page=None,
                ),
                confidence=0.9,
            ))

            # Ensure we make progress - at minimum advance by chunk_size
            if overlap > 0 and start > 0:
                next_start = end - overlap
                if next_start <= start:
                    next_start = start + chunk_size
                start = next_start
            else:
                start = end

            idx += 1

        return chunks

    @staticmethod
    def chunk_by_sentence(
        text: str,
        sentences_per_chunk: int = 3,
    ) -> list[KnowledgeChunk]:
        """Chunk text by sentences."""
        # Simple sentence splitting
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks: list[KnowledgeChunk] = []
        current_chunk: list[str] = []
        current_offset = 0

        for idx, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            sentence_start = text.find(sentence, current_offset)
            sentence_end = sentence_start + len(sentence)

            current_chunk.append(sentence.strip())

            if len(current_chunk) >= sentences_per_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(KnowledgeChunk(
                    chunk_id=f"sent_{idx}",
                    modality="text",
                    text=chunk_text,
                    metadata={"strategy": "sentence", "sentences": sentences_per_chunk},
                    source_span=SourceSpan(
                        start_offset=sentence_start,
                        end_offset=sentence_end,
                        line_start=0,
                        line_end=0,
                        page=None,
                    ),
                    confidence=0.95,  # High confidence for sentence boundaries
                ))
                current_chunk = []

            current_offset = sentence_end

        # Handle remaining sentences
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(KnowledgeChunk(
                chunk_id=f"sent_{len(sentences)}",
                modality="text",
                text=chunk_text,
                metadata={"strategy": "sentence", "sentences": len(current_chunk)},
                confidence=0.95,
            ))

        return chunks
