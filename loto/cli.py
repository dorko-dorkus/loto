"""Command line entry points for the LOTO planner.

This module defines a basic command line interface for running the LOTO
planner. It parses arguments, orchestrates the loading of rules,
building graphs, computing isolation plans, running simulations, and
producing outputs. Only a skeleton structure is provided here.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Optional
from uuid import uuid4

import networkx as nx
import typer
import yaml
from tqdm import tqdm

from .constants import DOC_CATEGORY_DIR
from .graph_builder import GraphBuilder
from .isolation_planner import IsolationPlanner
from .models import SimReport, Stimulus
from .renderer import Renderer
from .rule_engine import RuleEngine
from .sim_engine import SimEngine

cli = typer.Typer()


@cli.callback()
def main_callback() -> None:
    """LOTO command line interface."""
    return None


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Parameters
    ----------
    args: Optional[list[str]]
        Arguments to parse, defaults to None which uses sys.argv.

    Returns
    -------
    argparse.Namespace
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="LOTO planner CLI")
    parser.add_argument("--asset", help="Asset tag to isolate")
    parser.add_argument("--rules", help="Path to rule pack file (YAML/JSON)")
    parser.add_argument("--line-list", help="Path to line list CSV")
    parser.add_argument("--valves", help="Path to valves CSV")
    parser.add_argument("--drains", help="Path to drains/vents CSV")
    parser.add_argument("--sources", help="Path to energy sources CSV", default=None)
    parser.add_argument(
        "--air-map", help="Path to instrument air map CSV", default=None
    )
    parser.add_argument("--hazards", help="Path to hazards file", default=None)
    parser.add_argument("--controls", help="Path to controls file", default=None)
    parser.add_argument("--output", help="Directory for outputs", default="./out")
    parser.add_argument("--no-sim", action="store_true", help="Skip simulation testing")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode")

    parsed = parser.parse_args(args)

    if not parsed.demo:
        required = ["asset", "rules", "line_list", "valves", "drains"]
        missing = [opt for opt in required if getattr(parsed, opt) is None]
        if missing:
            parser.error(
                "Missing required arguments: "
                + ", ".join("--" + m.replace("_", "-") for m in missing)
            )

    return parsed


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the CLI.

    This function orchestrates the high-level flow: load rules, build
    graphs, compute the isolation plan, optionally run simulations,
    and render outputs. Method bodies are left as placeholders.
    """
    args = parse_args(argv)

    if args.demo:
        demo_dir = Path(__file__).resolve().parent.parent / "demo"
        args.asset = args.asset or "A"
        args.rules = args.rules or str(demo_dir / "rules.yaml")
        args.line_list = args.line_list or str(demo_dir / "line_list.csv")
        args.valves = args.valves or str(demo_dir / "valves.csv")
        args.drains = args.drains or str(demo_dir / "drains.csv")
        args.sources = args.sources or str(demo_dir / "sources.csv")
        args.hazards = args.hazards or str(demo_dir / "hazards.yaml")
        args.controls = args.controls or str(demo_dir / "controls.yaml")

    # Instantiate engine components
    rule_engine = RuleEngine()
    graph_builder = GraphBuilder()
    planner = IsolationPlanner()
    sim = SimEngine()
    renderer = Renderer()

    # Load rule pack, falling back to an empty pack if necessary
    try:
        rule_pack = rule_engine.load(args.rules)
    except Exception:  # pragma: no cover - graceful fallback
        from .models import RulePack

        # Explicitly set default fields to satisfy type checkers
        rule_pack = RulePack(domain_rules=[], verification_rules=[], risk_policies=None)

    # Build graphs from CSVs.  The builder is currently unimplemented, so fall
    # back to a minimal graph that contains a single source feeding the asset.
    try:
        graphs = graph_builder.from_csvs(
            args.line_list,
            args.valves,
            args.drains,
            args.sources,
            args.air_map,
        )
        if args.demo:
            for g in graphs.values():
                for u, v, data in g.edges(data=True):
                    if g.nodes[u].get("is_isolation_point") or g.nodes[v].get(
                        "is_isolation_point"
                    ):
                        data["is_isolation_point"] = True
    except Exception:  # pragma: no cover - use dummy graphs when builder missing
        g = nx.MultiDiGraph()
        g.add_node("source", is_source=True)
        g.add_node(args.asset, tag=args.asset)
        g.add_edge("source", args.asset, is_isolation_point=True)
        graphs = {"default": g}

    # Compute the isolation plan
    plan = planner.compute(graphs, args.asset, rule_pack)

    # Load hazards and controls if provided
    if args.hazards:
        try:
            with Path(args.hazards).open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or []
                if isinstance(data, list):
                    plan.hazards.extend(str(item) for item in data)
        except Exception:  # pragma: no cover - ignore loading failures
            pass
    if args.controls:
        try:
            with Path(args.controls).open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or []
                if isinstance(data, list):
                    plan.controls.extend(str(item) for item in data)
        except Exception:  # pragma: no cover - ignore loading failures
            pass

    # Run simulation if not skipped.  If the simulation engine is not
    # implemented, keep an empty report.
    sim_report: SimReport = SimReport(results=[], total_time_s=0.0, seed=None)
    if not args.no_sim:
        try:
            applied_graphs = sim.apply(plan, graphs)
            default_stimuli = [
                Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0),
                Stimulus(name="LOCAL_OPEN", magnitude=1.0, duration_s=1.0),
            ]
            sim_report = sim.run_stimuli(applied_graphs, default_stimuli, rule_pack)
        except Exception:  # pragma: no cover - ignore simulation failures
            pass

    # Render outputs
    json_output = renderer.to_json(plan, sim_report)
    json_output["category"] = "Permit/LOTO"
    rule_hash = rule_engine.hash(rule_pack)
    pdf_bytes = renderer.pdf(plan, sim_report, rule_hash, seed=None, timezone="UTC")

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"LOTO_{args.asset}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2)

    pdf_path = out_dir / f"LOTO_{args.asset}.pdf"
    with pdf_path.open("wb") as f:
        f.write(pdf_bytes)

    return None


@cli.command()
def demo(out: Path = Path("./out"), open_pdf: bool = False) -> None:
    """Generate demo PDF and JSON outputs."""
    try:
        with tqdm(total=1, desc="Generating demo", unit="step") as progress:
            main(["--demo", "--output", str(out)])
            progress.update(1)

        doclinks_dir = out / "doclinks" / DOC_CATEGORY_DIR
        doclinks_dir.mkdir(parents=True, exist_ok=True)
        doc_id = uuid4().hex
        shutil.copy(out / "LOTO_A.pdf", doclinks_dir / f"{doc_id}.pdf")
        shutil.copy(out / "LOTO_A.json", doclinks_dir / f"{doc_id}.json")

        typer.echo(f"✅ PDF + JSON saved to {out}")
        if open_pdf:
            pdf_path = out / "LOTO_A.pdf"
            try:
                typer.launch(str(pdf_path))
            except Exception:  # pragma: no cover - opening may fail in CI
                pass
    except Exception as exc:  # pragma: no cover - ensure friendly error
        typer.secho(f"Error: {exc}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    cli()
