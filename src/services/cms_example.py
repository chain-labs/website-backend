"""
example_use_cms.py

Demonstrates how to use the async, pure-function CMS service in cms_case_studies.py.

Run:
    python example_use_cms.py
    # or with custom options:
    python example_use_cms.py --latency 150 --single-id case-2 --ids case-3 case-1 case-3
"""

from __future__ import annotations

import argparse
import asyncio
import textwrap
from typing import Dict, Any, Iterable, List, Optional

from src.services.cms_case_studies import cms


def _brief(cs: Dict[str, Any], max_desc_chars: int = 160) -> str:
    """Create a single-line friendly summary of a case study."""
    desc = cs.get("description") or ""
    # Strip markdown-ish noise for terminal preview:
    desc_clean = " ".join(desc.replace("\n", " ").split())
    desc_short = textwrap.shorten(desc_clean, width=max_desc_chars, placeholder=" …")
    return f"- {cs['id']} | {cs['title']} :: {cs['shortDescription']} | {desc_short}"


def _print_list(label: str, items: Iterable[Dict[str, Any]]) -> None:
    print(f"\n{label}:")
    for cs in items:
        print(_brief(cs))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Example: use the CMS case studies service.")
    parser.add_argument("--latency", type=int, default=0, help="Simulated network latency in ms.")
    parser.add_argument("--single-id", type=str, default="case-2", help="ID to fetch with get_case_study_by_id.")
    parser.add_argument(
        "--ids",
        nargs="*",
        default=["case-3", "case-1", "case-3"],
        help="IDs to fetch with get_case_studies_by_ids.",
    )
    args = parser.parse_args()

    # Explicitly connect (the service also auto-connects if needed).
    await cms.connect(latency_ms=args.latency)

    # 1) Get all case studies
    all_cs = await cms.get_all_case_studies(simulate_latency_ms=args.latency)
    _print_list(f"All case studies (count={len(all_cs)})", all_cs)

    # 2) Get a single case study by ID
    one: Optional[Dict[str, Any]] = await cms.get_case_study_by_id(
        args.single_id, simulate_latency_ms=args.latency
    )
    print(f"\nSingle case study by id='{args.single_id}':")
    if one is None:
        print(f"- Not found: {args.single_id}")
    else:
        print(_brief(one))

    # 3) Get multiple by IDs (deduplicated, preserving order)
    many_dedupe: List[Dict[str, Any]] = await cms.get_case_studies_by_ids(
        args.ids, preserve_order=True, deduplicate=True, simulate_latency_ms=args.latency
    )
    _print_list("Multiple (preserve_order=True, deduplicate=True)", many_dedupe)

    # 4) Same list but without deduplication (to show duplicate handling)
    many_no_dedupe: List[Dict[str, Any]] = await cms.get_case_studies_by_ids(
        args.ids, preserve_order=True, deduplicate=False, simulate_latency_ms=args.latency
    )
    _print_list("Multiple (preserve_order=True, deduplicate=False)", many_no_dedupe)

    # 5) Fetch in parallel (demonstrates async usage)
    #    Here we request:
    #       - all case studies
    #       - a single (possibly missing) id
    #       - a shuffled set of ids
    tasks = [
        cms.get_all_case_studies(simulate_latency_ms=args.latency),
        cms.get_case_study_by_id("missing-id", simulate_latency_ms=args.latency),
        cms.get_case_studies_by_ids(["case-1", "case-2"], simulate_latency_ms=args.latency),
    ]
    all_again, missing, picked = await asyncio.gather(*tasks)

    print("\nParallel fetch results:")
    print(f"- all_again count: {len(all_again)}")
    print(f"- missing id result: {missing}")
    _print_list("- picked ids", picked)

    # Clean up (optional)
    await cms.disconnect()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
