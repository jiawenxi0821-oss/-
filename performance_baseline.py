#!/usr/bin/env python3
"""Performance baseline for QR generation."""

from __future__ import annotations

import statistics
import tracemalloc
from pathlib import Path
from time import perf_counter
from typing import Any

from generate_qrcode import build_about_page_url, generate_qrcode_for_url


def run_performance_baseline(
    *,
    base_url: str,
    output_dir: str = "output/perf",
    runs: int = 5,
    size: int = 10,
    border: int = 2,
) -> dict[str, Any]:
    if runs < 1:
        raise ValueError("runs 必须大于等于 1")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    full_url = build_about_page_url(base_url=base_url)

    elapsed_ms: list[float] = []
    file_sizes: list[int] = []

    tracemalloc.start()
    for idx in range(runs):
        output_path = out_dir / f"perf_{idx + 1}.png"
        started = perf_counter()
        generated = generate_qrcode_for_url(
            full_url=full_url,
            output_path=str(output_path),
            size=size,
            border=border,
            quiet=True,
        )
        elapsed_ms.append(round((perf_counter() - started) * 1000, 3))
        file_sizes.append(int(generated.stat().st_size))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "runs": runs,
        "target_url": full_url,
        "output_dir": str(out_dir.resolve()),
        "elapsed_ms": {
            "min": min(elapsed_ms),
            "max": max(elapsed_ms),
            "avg": round(statistics.mean(elapsed_ms), 3),
            "p95_approx": round(sorted(elapsed_ms)[max(0, int(runs * 0.95) - 1)], 3),
        },
        "file_size_bytes": {
            "min": min(file_sizes),
            "max": max(file_sizes),
            "avg": round(statistics.mean(file_sizes), 1),
        },
        "memory_peak_kb": round(peak / 1024, 2),
    }

