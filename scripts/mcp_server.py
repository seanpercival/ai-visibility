#!/usr/bin/env python3
"""
mcp_server.py - Optional MCP server exposing the AEO scanner as callable tools.

Makes scan_site / generate_panel available from any MCP-capable client
(Claude Desktop, Claude Code, etc.), so "scan this URL" works without shelling
out to the scripts.

Requires the MCP SDK (the ONLY dependency in this skill):
    pip install "mcp[cli]"

Run:
    python3 mcp_server.py            # stdio transport

Register in an MCP client (example Claude Desktop config):
    "ai-visibility": {
      "command": "python3",
      "args": ["/absolute/path/to/ai-visibility/scripts/mcp_server.py"]
    }
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan          # local, zero-dependency
import prompt_panel  # local

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.stderr.write('MCP SDK not installed. Run: pip install "mcp[cli]"\n')
    sys.exit(1)

mcp = FastMCP("ai-visibility")


@mcp.tool()
def scan_site(url: str, brand: str = "", check_offsite: bool = True) -> dict:
    """Run the 31-point AEO scan on a URL. Returns score, pillar breakdown,
    and per-check findings. `brand` enables Wikipedia/Wikidata/Reddit/review
    checks. Access is a gate: blocked AI crawlers cap the score at 40."""
    if not url.startswith("http"):
        url = "https://" + url
    results, meta = scan.run_checks(url, brand.strip(), check_offsite)
    total, by, gate = scan.score(results)
    return {
        "url": meta["final_url"],
        "brand": brand,
        "score": total,
        "band": scan.band(total),
        "access_gate_failed": gate,
        "pillars": {p: {"points": d["pts"], "max": d["max"]} for p, d in by.items()},
        "findings": [
            {"pillar": r["pillar"], "status": r["status"], "finding": r["msg"], "fix": r["fix"]}
            for r in results
        ],
        "note": "On-site + entity signals only. Run a prompt panel for live share of voice. Frequency, not rank.",
    }


@mcp.tool()
def generate_panel(brand: str, competitors: str = "", category: str = "") -> dict:
    """Generate a measurement prompt panel (category / alternative / use-case /
    brand / trust buckets) for measuring share of voice in AI answers."""
    comps = [c.strip() for c in competitors.split(",") if c.strip()]
    return prompt_panel.generate_panel(brand, comps, category)


if __name__ == "__main__":
    mcp.run()
