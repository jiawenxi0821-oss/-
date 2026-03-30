#!/usr/bin/env python3
"""Batch QR code generation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from generate_qrcode import generate_about_us_qrcode
from qrcode_config import QRStyleConfig


def generate_batch_qrcodes(
    *,
    base_url: str,
    page_path: str,
    default_style: QRStyleConfig,
    profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate multiple QR images with style overrides.

    A failure in one profile does not stop the rest.
    """
    results: list[dict[str, Any]] = []

    for idx, profile in enumerate(profiles):
        name = str(profile.get("name", f"profile_{idx + 1}"))
        output_path = profile.get("output_path") or f"output/about_us_{name}.png"
        try:
            style = default_style.merged({**profile, "output_path": output_path})
            generated_file = generate_about_us_qrcode(
                base_url=base_url,
                output_path=style.output_path,
                size=style.size,
                border=style.border,
                fill_color=style.fill_color,
                back_color=style.back_color,
                page_path=page_path,
            )
            results.append(
                {
                    "name": name,
                    "success": True,
                    "output_path": str(Path(generated_file).resolve()),
                    "error": "",
                }
            )
        except Exception as exc:
            results.append(
                {
                    "name": name,
                    "success": False,
                    "output_path": str(output_path),
                    "error": str(exc),
                }
            )

    total = len(results)
    success_count = sum(1 for row in results if row["success"])
    failed_count = total - success_count

    return {
        "total": total,
        "success": success_count,
        "failed": failed_count,
        "results": results,
    }

