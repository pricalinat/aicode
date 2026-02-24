from __future__ import annotations

import argparse
import json
import sys

from .agents import ArxivAgent, PaperSearchAgent
from .core import Message, Orchestrator


def build_parser() -> argparse.ArgumentParser:
    """Build the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Multi-agent arXiv paper search and management"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search command (original functionality)
    search_parser = subparsers.add_parser("search-arxiv", help="Search arXiv papers")
    search_parser.add_argument("--query", required=True, help="Search query text")
    search_parser.add_argument("--category", default=None, help="arXiv category, e.g. cs.CL")
    search_parser.add_argument("--start-year", type=int, default=None, help="Filter start year")
    search_parser.add_argument("--end-year", type=int, default=None, help="Filter end year")
    search_parser.add_argument("--max-results", type=int, default=10, help="Max results (1-100)")
    search_parser.add_argument(
        "--sort-by",
        choices=["relevance", "lastUpdatedDate", "submittedDate"],
        default="relevance",
    )
    search_parser.add_argument(
        "--sort-order",
        choices=["ascending", "descending"],
        default="descending",
    )

    # Save command - save papers to local repository
    save_parser = subparsers.add_parser("save", help="Save papers from arXiv search to local storage")
    save_parser.add_argument("--query", required=True, help="Search query text")
    save_parser.add_argument("--category", default=None, help="arXiv category, e.g. cs.CL")
    save_parser.add_argument("--start-year", type=int, default=None, help="Filter start year")
    save_parser.add_argument("--end-year", type=int, default=None, help="Filter end year")
    save_parser.add_argument("--max-results", type=int, default=10, help="Max results (1-100)")
    save_parser.add_argument(
        "--sort-by",
        choices=["relevance", "lastUpdatedDate", "submittedDate"],
        default="relevance",
    )
    save_parser.add_argument(
        "--sort-order",
        choices=["ascending", "descending"],
        default="descending",
    )

    # List command - list saved papers
    list_parser = subparsers.add_parser("list", help="List saved papers")
    list_parser.add_argument("--category", default=None, help="Filter by category")
    list_parser.add_argument("--year", type=int, default=None, help="Filter by year")
    list_parser.add_argument("--author", default=None, help="Filter by author")
    list_parser.add_argument("--limit", type=int, default=100, help="Max papers to list")

    # Semantic search command - search saved papers
    semantic_parser = subparsers.add_parser(
        "semantic-search", help="Semantic search in saved papers"
    )
    semantic_parser.add_argument("query", help="Search query text")
    semantic_parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    semantic_parser.add_argument("--category", default=None, help="Filter by category")
    semantic_parser.add_argument("--year", type=int, default=None, help="Filter by year")

    # Count command - count saved papers
    count_parser = subparsers.add_parser("count", help="Count saved papers")

    # Clear command - clear all saved papers
    clear_parser = subparsers.add_parser("clear", help="Clear all saved papers")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Default to search-arxiv if no command provided (backward compatibility)
    if args.command is None:
        # Fall back to old behavior for backward compatibility
        args.command = "search-arxiv"
        # Re-parse with old defaults
        old_parser = argparse.ArgumentParser(description="Multi-agent arXiv paper search")
        old_parser.add_argument("--query", required=True, help="Search query text")
        old_parser.add_argument("--category", default=None, help="arXiv category, e.g. cs.CL")
        old_parser.add_argument("--start-year", type=int, default=None, help="Filter start year")
        old_parser.add_argument("--end-year", type=int, default=None, help="Filter end year")
        old_parser.add_argument("--max-results", type=int, default=10, help="Max results (1-100)")
        old_parser.add_argument(
            "--sort-by",
            choices=["relevance", "lastUpdatedDate", "submittedDate"],
            default="relevance",
        )
        old_parser.add_argument(
            "--sort-order",
            choices=["ascending", "descending"],
            default="descending",
        )
        try:
            args = old_parser.parse_args()
        except SystemExit:
            parser.print_help()
            return 1
        return search_arxiv(args)

    # Handle subcommands
    if args.command == "search-arxiv":
        return search_arxiv(args)
    elif args.command == "save":
        return save_papers(args)
    elif args.command == "list":
        return list_papers(args)
    elif args.command == "semantic-search":
        return semantic_search(args)
    elif args.command == "count":
        return count_papers(args)
    elif args.command == "clear":
        return clear_papers(args)
    else:
        parser.print_help()
        return 1


def search_arxiv(args) -> int:
    """Search arXiv papers."""
    orchestrator = Orchestrator([ArxivAgent()])
    message = Message(
        task_type="search_arxiv",
        content={
            "query": args.query,
            "category": args.category,
            "start_year": args.start_year,
            "end_year": args.end_year,
            "max_results": args.max_results,
            "sort_by": args.sort_by,
            "sort_order": args.sort_order,
        },
    )
    response = orchestrator.dispatch(message)
    if not response.success:
        print(json.dumps({"trace_id": response.trace_id, "error": response.error}, ensure_ascii=False))
        return 1

    print(json.dumps(response.data, ensure_ascii=False, indent=2))
    return 0


def save_papers(args) -> int:
    """Save papers from arXiv search to local storage."""
    # First, search arXiv
    orchestrator = Orchestrator([ArxivAgent()])
    message = Message(
        task_type="search_arxiv",
        content={
            "query": args.query,
            "category": args.category,
            "start_year": args.start_year,
            "end_year": args.end_year,
            "max_results": args.max_results,
            "sort_by": args.sort_by,
            "sort_order": args.sort_order,
        },
    )
    response = orchestrator.dispatch(message)
    if not response.success:
        print(json.dumps({"error": response.error}, ensure_ascii=False))
        return 1

    papers = response.data.get("papers", [])
    if not papers:
        print(json.dumps({"message": "No papers found to save"}, ensure_ascii=False))
        return 0

    # Save to repository
    paper_agent = PaperSearchAgent()
    save_message = Message(
        task_type="paper_search",
        content={
            "action": "save",
            "papers": papers,
        },
    )
    save_response = paper_agent.handle(save_message)

    if not save_response.success:
        print(json.dumps({"error": save_response.error}, ensure_ascii=False))
        return 1

    print(json.dumps(save_response.data, ensure_ascii=False, indent=2))
    return 0


def list_papers(args) -> int:
    """List saved papers."""
    paper_agent = PaperSearchAgent()
    message = Message(
        task_type="paper_search",
        content={
            "action": "list",
            "category": args.category,
            "year": args.year,
            "author": args.author,
            "limit": args.limit,
        },
    )
    response = paper_agent.handle(message)

    if not response.success:
        print(json.dumps({"error": response.error}, ensure_ascii=False))
        return 1

    print(json.dumps(response.data, ensure_ascii=False, indent=2))
    return 0


def semantic_search(args) -> int:
    """Semantic search in saved papers."""
    paper_agent = PaperSearchAgent()
    message = Message(
        task_type="paper_search",
        content={
            "action": "search",
            "query": args.query,
            "top_k": args.top_k,
            "category": args.category,
            "year": args.year,
        },
    )
    response = paper_agent.handle(message)

    if not response.success:
        print(json.dumps({"error": response.error}, ensure_ascii=False))
        return 1

    print(json.dumps(response.data, ensure_ascii=False, indent=2))
    return 0


def count_papers(args) -> int:
    """Count saved papers."""
    paper_agent = PaperSearchAgent()
    message = Message(
        task_type="paper_search",
        content={"action": "count"},
    )
    response = paper_agent.handle(message)

    if not response.success:
        print(json.dumps({"error": response.error}, ensure_ascii=False))
        return 1

    print(json.dumps(response.data, ensure_ascii=False, indent=2))
    return 0


def clear_papers(args) -> int:
    """Clear all saved papers."""
    paper_agent = PaperSearchAgent()
    message = Message(
        task_type="paper_search",
        content={"action": "clear"},
    )
    response = paper_agent.handle(message)

    if not response.success:
        print(json.dumps({"error": response.error}, ensure_ascii=False))
        return 1

    print(json.dumps({"message": "All papers cleared"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
