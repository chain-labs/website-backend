"""
cms_case_studies.py

Async, pure-function "CMS" service for fetching case studies.
- No classes, just functions.
- In-memory dictionary simulates the CMS for now.
- Descriptions use Markdown and are >= 500 words each.
"""

from __future__ import annotations

import asyncio
import copy
from typing import Any, Dict, Iterable, List, Optional
from .dummyCms import _CASE_STUDIES

__all__ = [
    "connect",
    "disconnect",
    "is_connected",
    "get_all_case_studies",
    "get_case_study_by_id",
    "get_case_studies_by_ids",
]

# ------------------------------------------------------------------------------
# Simulated CMS connection state
# ------------------------------------------------------------------------------

_CONNECTED: bool = False


async def connect(*, latency_ms: int = 0) -> None:
    """
    "Connect" to the CMS (simulated). Optionally await a tiny artificial latency.

    Args:
        latency_ms: Optional simulated latency to await before marking connected.
    """
    global _CONNECTED
    if latency_ms:
        await asyncio.sleep(latency_ms / 1000)
    _CONNECTED = True


async def disconnect() -> None:
    """Disconnect from the CMS (simulated)."""
    global _CONNECTED
    _CONNECTED = False
    await asyncio.sleep(0)


def is_connected() -> bool:
    """Return True if the simulated CMS is connected."""
    return _CONNECTED


async def _ensure_connected() -> None:
    """
    Internal helper that ensures the "CMS" is connected.
    If not connected, auto-connect with no latency.
    """
    global _CONNECTED
    if not _CONNECTED:
        await connect()




# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

DEFAULT_FALLBACK_IMAGE = "https://images.unsplash.com/photo-1752578753798-ff3a23e16498?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"

# ------------------------------------------------------------------------------
# Public API (async, pure functions)
# ------------------------------------------------------------------------------

async def get_all_case_studies(*, simulate_latency_ms: int = 0) -> List[Dict[str, Any]]:
    """
    Return all case studies as a list (deep copies), preserving insertion order.

    Args:
        simulate_latency_ms: Optional artificial latency to mimic network I/O.

    Returns:
        List of case study dictionaries.
    """
    await _ensure_connected()
    if simulate_latency_ms:
        await asyncio.sleep(simulate_latency_ms / 1000)
    case_studies = [copy.deepcopy(v) for v in _CASE_STUDIES.values()]
    
    # Add fallback image to each case study
    for case_study in case_studies:
        case_study["fallbackImage"] = DEFAULT_FALLBACK_IMAGE
    
    return case_studies


async def get_case_study_by_id(case_id: str, *, simulate_latency_ms: int = 0) -> Optional[Dict[str, Any]]:
    """
    Return a single case study by ID (deep copy), or None if not found.

    Args:
        case_id: The case study identifier.
        simulate_latency_ms: Optional artificial latency to mimic network I/O.

    Returns:
        Dict for the case study, or None if missing.
    """
    await _ensure_connected()
    if simulate_latency_ms:
        await asyncio.sleep(simulate_latency_ms / 1000)
    data = _CASE_STUDIES.get(case_id)
    if data is not None:
        case_study = copy.deepcopy(data)
        case_study["fallbackImage"] = DEFAULT_FALLBACK_IMAGE
        return case_study
    return None


async def get_case_studies_by_ids(
    ids: Iterable[str],
    *,
    preserve_order: bool = True,
    deduplicate: bool = True,
    simulate_latency_ms: int = 0,
) -> List[Dict[str, Any]]:
    """
    Return multiple case studies given an iterable of IDs.

    Args:
        ids: Iterable of case IDs to fetch.
        preserve_order: If True, return results in the same order as `ids`.
        deduplicate: If True, repeated IDs are fetched once in the returned list.
        simulate_latency_ms: Optional artificial latency to mimic network I/O.

    Returns:
        List of case study dictionaries found for the given IDs. Missing IDs are skipped.
    """
    await _ensure_connected()
    if simulate_latency_ms:
        await asyncio.sleep(simulate_latency_ms / 1000)

    if preserve_order:
        seen = set()
        results: List[Dict[str, Any]] = []
        for cid in ids:
            if deduplicate and cid in seen:
                continue
            item = _CASE_STUDIES.get(cid)
            if item is not None:
                case_study = copy.deepcopy(item)
                case_study["fallbackImage"] = DEFAULT_FALLBACK_IMAGE
                results.append(case_study)
                seen.add(cid)
        return results
    else:
        # Unordered: just collect unique (or not) and return
        out: List[Dict[str, Any]] = []
        seen = set()
        for cid in ids:
            if deduplicate and cid in seen:
                continue
            item = _CASE_STUDIES.get(cid)
            if item is not None:
                case_study = copy.deepcopy(item)
                case_study["fallbackImage"] = DEFAULT_FALLBACK_IMAGE
                out.append(case_study)
                seen.add(cid)
        return out
