from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from ..core.agent import AgentResponse, BaseAgent
from ..core.message import Message


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


@dataclass
class ArxivSearchInput:
    query: str
    category: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    max_results: int = 10
    sort_by: str = "relevance"
    sort_order: str = "descending"

    @classmethod
    def from_content(cls, content: dict[str, Any]) -> "ArxivSearchInput":
        query = str(content.get("query", "")).strip()
        if not query:
            raise ValueError("content.query is required")

        category = content.get("category")
        start_year = content.get("start_year")
        end_year = content.get("end_year")
        max_results = int(content.get("max_results", 10))
        sort_by = str(content.get("sort_by", "relevance"))
        sort_order = str(content.get("sort_order", "descending"))

        if max_results < 1:
            raise ValueError("max_results must be >= 1")
        if max_results > 100:
            max_results = 100

        if sort_by not in {"relevance", "lastUpdatedDate", "submittedDate"}:
            raise ValueError("sort_by must be one of relevance|lastUpdatedDate|submittedDate")
        if sort_order not in {"ascending", "descending"}:
            raise ValueError("sort_order must be one of ascending|descending")

        return cls(
            query=query,
            category=str(category) if category else None,
            start_year=int(start_year) if start_year is not None else None,
            end_year=int(end_year) if end_year is not None else None,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )


class ArxivAgent(BaseAgent):
    name = "arxiv-agent"
    capabilities = {"search_arxiv", "arxiv_search", "paper_search"}
    endpoint = "https://export.arxiv.org/api/query"

    def handle(self, message: Message) -> AgentResponse:
        try:
            params = ArxivSearchInput.from_content(message.content)
            query = self._build_search_query(params)
            raw_xml = self._query_arxiv(
                search_query=query,
                max_results=params.max_results,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )
            papers = self._parse_feed(raw_xml)
            return AgentResponse(
                agent=self.name,
                success=True,
                data={
                    "count": len(papers),
                    "query": query,
                    "papers": papers,
                },
                trace_id=message.trace_id,
            )
        except Exception as exc:  # pragma: no cover - defensive branch
            return AgentResponse(
                agent=self.name,
                success=False,
                error=str(exc),
                trace_id=message.trace_id,
            )

    def _build_search_query(self, params: ArxivSearchInput) -> str:
        parts: list[str] = []

        safe_query = params.query.replace('"', "")
        if " " in safe_query:
            parts.append(f'all:"{safe_query}"')
        else:
            parts.append(f"all:{safe_query}")

        if params.category:
            parts.append(f"cat:{params.category}")

        if params.start_year is not None or params.end_year is not None:
            start_year = params.start_year if params.start_year is not None else 1991
            end_year = params.end_year if params.end_year is not None else 2100
            if start_year > end_year:
                raise ValueError("start_year cannot be greater than end_year")
            start = f"{start_year}01010000"
            end = f"{end_year}12312359"
            parts.append(f"submittedDate:[{start} TO {end}]")

        return " AND ".join(parts)

    def _query_arxiv(
        self,
        *,
        search_query: str,
        max_results: int,
        sort_by: str,
        sort_order: str,
    ) -> str:
        query_params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        url = f"{self.endpoint}?{urlencode(query_params)}"
        req = Request(
            url=url,
            headers={"User-Agent": "multi-agent-arxiv/0.1 (+https://arxiv.org)"},
        )
        with urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8")

    def _parse_feed(self, raw_xml: str) -> list[dict[str, Any]]:
        root = ET.fromstring(raw_xml)
        entries = root.findall("atom:entry", namespaces=ATOM_NS)
        papers: list[dict[str, Any]] = []

        for entry in entries:
            title = self._node_text(entry, "atom:title")
            summary = self._node_text(entry, "atom:summary")
            paper_id = self._node_text(entry, "atom:id")
            published = self._node_text(entry, "atom:published")
            updated = self._node_text(entry, "atom:updated")
            authors = [
                (author.find("atom:name", namespaces=ATOM_NS).text or "").strip()
                for author in entry.findall("atom:author", namespaces=ATOM_NS)
                if author.find("atom:name", namespaces=ATOM_NS) is not None
            ]
            categories = [
                (cat.attrib.get("term", "")).strip()
                for cat in entry.findall("atom:category", namespaces=ATOM_NS)
                if cat.attrib.get("term")
            ]
            primary = entry.find("arxiv:primary_category", namespaces=ATOM_NS)
            primary_category = primary.attrib.get("term", "").strip() if primary is not None else None
            pdf_url = self._extract_pdf_url(entry) or paper_id

            papers.append(
                {
                    "id": paper_id,
                    "title": " ".join(title.split()),
                    "summary": " ".join(summary.split()),
                    "authors": authors,
                    "published": published,
                    "updated": updated,
                    "pdf_url": pdf_url,
                    "categories": categories,
                    "primary_category": primary_category,
                }
            )

        return papers

    def _node_text(self, entry: ET.Element, path: str) -> str:
        node = entry.find(path, namespaces=ATOM_NS)
        if node is None or node.text is None:
            return ""
        return node.text.strip()

    def _extract_pdf_url(self, entry: ET.Element) -> str | None:
        for link in entry.findall("atom:link", namespaces=ATOM_NS):
            if link.attrib.get("title") == "pdf":
                href = link.attrib.get("href")
                if href:
                    return href.strip()
        return None
