"""
CLI dispatch for ``myco graph`` — link graph analysis.

Wave 47 (contract v0.36.0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from myco.project import resolve_project_dir




def run_graph(args: Any) -> int:
    """Dispatch ``myco graph`` subcommands."""
    from myco.mycelium import (
        build_link_graph,
        find_clusters,
        find_orphans,
        graph_stats,
        query_backlinks,
    )

    root = resolve_project_dir(args, strict=False)
    use_json = getattr(args, "json", False)
    sub = getattr(args, "graph_subcommand", None)

    if sub is None:
        print("Usage: myco graph {backlinks|orphans|clusters|stats}", file=sys.stderr)
        return 1

    graph = build_link_graph(root)

    if sub == "backlinks":
        target = getattr(args, "file", None)
        if not target:
            print("Usage: myco graph backlinks <file>", file=sys.stderr)
            return 1
        target = target.replace("\\", "/")
        bl = query_backlinks(graph, target)
        if use_json:
            print(json.dumps({"target": target, "backlinks": bl}, indent=2))
        else:
            if bl:
                print(f"Backlinks to {target} ({len(bl)}):")
                for src in bl:
                    print(f"  ← {src}")
            else:
                print(f"No backlinks found for {target}")
        return 0

    if sub == "orphans":
        orphans = find_orphans(graph)
        if use_json:
            print(json.dumps({"orphans": orphans, "count": len(orphans)}, indent=2))
        else:
            if orphans:
                print(f"Orphan files ({len(orphans)}) — zero inbound links:")
                for o in orphans:
                    print(f"  ⊘ {o}")
            else:
                print("No orphan files found.")
        return 0

    if sub == "clusters":
        clusters = find_clusters(graph)
        if use_json:
            print(json.dumps({
                "clusters": clusters,
                "cluster_count": len(clusters),
            }, indent=2))
        else:
            print(f"Connected components: {len(clusters)}")
            for i, cluster in enumerate(clusters):
                print(f"\n  Cluster {i + 1} ({len(cluster)} files):")
                for f in cluster[:10]:
                    print(f"    • {f}")
                if len(cluster) > 10:
                    print(f"    … and {len(cluster) - 10} more")
        return 0

    if sub == "stats":
        stats = graph_stats(graph)
        if use_json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"Link graph statistics:")
            print(f"  Nodes:    {stats['total_nodes']}")
            print(f"  Edges:    {stats['total_edges']}")
            print(f"  Orphans:  {stats['orphan_count']}")
            print(f"  Clusters: {stats['cluster_count']}")
            print(f"  Hub:      {stats['hub']['file']} "
                  f"({stats['hub']['backlink_count']} backlinks)")
            print(f"  Authority:{stats['authority']['file']} "
                  f"({stats['authority']['forward_count']} forward links)")
        return 0

    print(f"Unknown subcommand: {sub}", file=sys.stderr)
    return 1
