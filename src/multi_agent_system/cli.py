from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agents import ArxivAgent, PaperSearchAgent
from .closed_loop import (
    FeatureStore,
    FeedbackLoop,
    SyntheticSupplyGenerator,
    SyntheticUserBehaviorGenerator,
)
from .core import Message, Orchestrator
from .experiments import OfflineABRunner
from .knowledge.supply_graph_database import SupplyGraphDatabase
from .knowledge.supply_graph_models import SupplyEntity, SupplyEntityType
from .matching import DualMatcher
from .reporting import ReportFormat, ReportGenerator, ReportType


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

    # Offline closed-loop demo
    closed_loop_parser = subparsers.add_parser(
        "build-closed-loop-demo", help="Build offline synthetic closed-loop demo data"
    )
    closed_loop_parser.add_argument("--seed", type=int, default=42)
    closed_loop_parser.add_argument("--supplies", type=int, default=16)
    closed_loop_parser.add_argument("--users", type=int, default=10)

    dual_parser = subparsers.add_parser(
        "run-dual-matching-demo", help="Run bidirectional matching demo"
    )
    dual_parser.add_argument("--top-k", type=int, default=5)

    ab_parser = subparsers.add_parser("run-offline-ab", help="Run offline A/B experiment")
    ab_parser.add_argument("--report-name", default="offline_ab_report.json")

    # Generate report command
    gen_report_parser = subparsers.add_parser("generate-report", help="Generate a report")
    gen_report_parser.add_argument("--type", required=True, choices=["test_analysis", "kg_health", "benchmark", "experiment"], help="Report type")
    gen_report_parser.add_argument("--format", default="markdown", choices=["markdown", "json", "html"], help="Output format")
    gen_report_parser.add_argument("--input", required=True, help="Input JSON file with report data")
    gen_report_parser.add_argument("--output", help="Output file (default: stdout)")

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
    elif args.command == "build-closed-loop-demo":
        return build_closed_loop_demo(args)
    elif args.command == "run-dual-matching-demo":
        return run_dual_matching_demo(args)
    elif args.command == "generate-report":
        return generate_report(args)
    elif args.command == "run-offline-ab":
        return run_offline_ab(args)
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


def _build_closed_loop(seed: int = 42, supplies: int = 16, users: int = 10) -> dict:
    supply_gen = SyntheticSupplyGenerator(seed=seed)
    generated = supply_gen.generate(num_supplies=supplies, num_users=users)
    behavior_gen = SyntheticUserBehaviorGenerator(seed=seed + 1)
    events = behavior_gen.generate(generated["users"], generated["supplies"], days=2)

    features = FeatureStore().build(generated["supplies"], events)

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "synthetic_supply.json").write_text(
        json.dumps(generated["supplies"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "synthetic_users.json").write_text(
        json.dumps(generated["users"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "synthetic_events.json").write_text(
        json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "feature_store_snapshot.json").write_text(
        json.dumps(list(features.values()), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "supplies": generated["supplies"],
        "users": generated["users"],
        "events": events,
        "features": features,
    }


def build_closed_loop_demo(args) -> int:
    artifact = _build_closed_loop(seed=args.seed, supplies=args.supplies, users=args.users)
    print(json.dumps({"message": "closed-loop demo built", "events": len(artifact["events"])}, ensure_ascii=False))
    return 0


def run_dual_matching_demo(args) -> int:
    artifact = _build_closed_loop()
    db = SupplyGraphDatabase()

    for s in artifact["supplies"]:
        db.create_entity(SupplyEntity(id=s["supply_id"], type=SupplyEntityType.PRODUCT, properties=s), validate=False)
    for u in artifact["users"]:
        db.create_entity(SupplyEntity(id=u["user_id"], type=SupplyEntityType.USER, properties=u), validate=False)

    matcher = DualMatcher(db=db, feature_map=artifact["features"])
    user_id = artifact["users"][0]["user_id"]
    supply_id = artifact["supplies"][0]["supply_id"]

    result = {
        "for_user": matcher.match_supply_for_user(user_id, {"top_k": args.top_k}),
        "for_supply": matcher.match_users_for_supply(supply_id, {"top_k": args.top_k}),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_offline_ab(args) -> int:
    artifact = _build_closed_loop()
    users = artifact["users"]
    supplies = [s["supply_id"] for s in artifact["supplies"]]

    baseline = {u["user_id"]: supplies[:5] for u in users}
    treatment = {u["user_id"]: supplies[1:6] for u in users}
    relevance = {
        u["user_id"]: {sid: (1.0 if sid in supplies[:3] else 0.2) for sid in supplies[:8]}
        for u in users
    }
    order_value_map = {s["supply_id"]: float(s.get("price", 0.0)) for s in artifact["supplies"]}

    runner = OfflineABRunner(output_dir=Path("data/experiments"))
    report = runner.run(
        baseline=baseline,
        treatment=treatment,
        relevance=relevance,
        events=artifact["events"],
        order_value_map=order_value_map,
        report_name=args.report_name,
    )

    feedback = {
        sid: {
            "reward": report["proxy"]["conversion"],
            "risk_violation": 0.0,
        }
        for sid in artifact["features"].keys()
    }
    updated = FeedbackLoop().apply(artifact["features"], feedback)
    (Path("data") / "feature_store_after_feedback.json").write_text(
        json.dumps(list(updated.values()), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def generate_report(args) -> int:
    """Generate a report from input data."""
    # Read input JSON file
    input_path = Path(args.input)
    if not input_path.exists():
        print(json.dumps({"error": f"Input file not found: {args.input}"}, ensure_ascii=False))
        return 1

    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}, ensure_ascii=False))
        return 1

    # Map report type
    type_map = {
        "test_analysis": ReportType.TEST_ANALYSIS,
        "kg_health": ReportType.KG_HEALTH,
        "benchmark": ReportType.BENCHMARK,
        "experiment": ReportType.EXPERIMENT,
    }
    format_map = {
        "markdown": ReportFormat.MARKDOWN,
        "json": ReportFormat.JSON,
        "html": ReportFormat.HTML,
    }

    report_type = type_map[args.type]
    output_format = format_map[args.format]

    # Generate report
    generator = ReportGenerator()
    output = generator.generate(
        report_type=report_type,
        data=data,
        format=output_format,
    )

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output, encoding="utf-8")
        print(json.dumps({"message": f"Report written to {args.output}"}, ensure_ascii=False))
    else:
        print(output)

    return 0
