#!/usr/bin/env python3
"""Unified CLI for About-Us QR generation and verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from batch_generate import generate_batch_qrcodes
from generate_qrcode import (
    DEFAULT_PAGE_PATH,
    build_about_page_url,
    generate_about_us_qrcode,
    generate_qrcode_for_url,
    normalize_page_path,
)
from qrcode_config import ConfigError, parse_runtime_config


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_logo_path(logo_arg: str = "") -> str | None:
    explicit = str(logo_arg).strip()
    if explicit:
        return explicit
    default_logo = Path("ui copy/logo.png")
    if default_logo.exists():
        return str(default_logo)
    return None


def _is_full_page_url(url: str, page_path: str) -> bool:
    normalized_path = normalize_page_path(page_path)
    return url.rstrip("/").endswith(normalized_path)


def cmd_generate(args: argparse.Namespace) -> int:
    target = str(args.url).strip()
    page_path = normalize_page_path(args.page_path)
    logo_path = _resolve_logo_path(args.logo)

    if _is_full_page_url(target, page_path=page_path):
        full_url = target
        output = generate_qrcode_for_url(
            full_url=full_url,
            output_path=args.output,
            size=args.size,
            border=args.border,
            fill_color=args.fill_color,
            back_color=args.back_color,
            logo_path=logo_path,
            logo_scale=args.logo_scale,
        )
    else:
        output = generate_about_us_qrcode(
            base_url=target,
            output_path=args.output,
            size=args.size,
            border=args.border,
            fill_color=args.fill_color,
            back_color=args.back_color,
            page_path=page_path,
            logo_path=logo_path,
            logo_scale=args.logo_scale,
        )
        full_url = build_about_page_url(target, page_path=page_path)

    _emit(
        {
            "ok": True,
            "mode": "generate",
            "full_url": full_url,
            "output_path": str(Path(output).resolve()),
            "logo_path": str(Path(logo_path).resolve()) if logo_path else "",
        }
    )
    return 0


def cmd_from_config(args: argparse.Namespace) -> int:
    runtime = parse_runtime_config(args.config)
    style = runtime.default_style
    output_path = args.output or style.output_path
    logo_path = _resolve_logo_path(args.logo)
    generated = generate_about_us_qrcode(
        base_url=runtime.base_url,
        output_path=output_path,
        size=style.size,
        border=style.border,
        fill_color=style.fill_color,
        back_color=style.back_color,
        page_path=runtime.page_path,
        logo_path=logo_path,
        logo_scale=args.logo_scale,
    )
    _emit(
        {
            "ok": True,
            "mode": "from-config",
            "config_path": str(runtime.config_path.resolve()),
            "full_url": build_about_page_url(runtime.base_url, runtime.page_path),
            "output_path": str(Path(generated).resolve()),
            "logo_path": str(Path(logo_path).resolve()) if logo_path else "",
        }
    )
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    runtime = parse_runtime_config(args.config)
    summary = generate_batch_qrcodes(
        base_url=runtime.base_url,
        page_path=runtime.page_path,
        default_style=runtime.default_style,
        profiles=runtime.batch_profiles,
    )
    _emit(
        {
            "ok": summary["failed"] == 0,
            "mode": "batch",
            "config_path": str(runtime.config_path.resolve()),
            **summary,
        }
    )
    return 0 if summary["failed"] == 0 else 1


def cmd_verify(args: argparse.Namespace) -> int:
    from verify_deployment import verify_deployment

    result = verify_deployment(
        expected_url=str(args.url).strip(),
        qrcode_path=args.qrcode,
        timeout_sec=args.timeout,
    )
    _emit({"mode": "verify", **result})
    return 0 if result["ok"] else 1


def cmd_perf(args: argparse.Namespace) -> int:
    from performance_baseline import run_performance_baseline

    result = run_performance_baseline(
        base_url=str(args.base_url).strip(),
        output_dir=args.output_dir,
        runs=args.runs,
        size=args.size,
        border=args.border,
    )
    _emit({"mode": "perf", "ok": True, **result})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qrcode_cli.py",
        description="About-Us QR code toolchain CLI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_generate = sub.add_parser("generate", help="Generate a single QR image from --url.")
    p_generate.add_argument("--url", required=True, help="Base URL or full about page URL.")
    p_generate.add_argument("--output", default="output/about_us_qrcode.png", help="PNG output path.")
    p_generate.add_argument("--size", type=int, default=10, help="QR box size [1-40].")
    p_generate.add_argument("--border", type=int, default=2, help="QR border width (>=0).")
    p_generate.add_argument("--fill-color", default="black", help="Foreground color.")
    p_generate.add_argument("--back-color", default="white", help="Background color.")
    p_generate.add_argument("--page-path", default=DEFAULT_PAGE_PATH, help="Page path (default /about.html).")
    p_generate.add_argument("--logo", default="", help="Center logo image path (PNG/JPG).")
    p_generate.add_argument(
        "--logo-scale",
        type=float,
        default=0.2,
        help="Center logo size ratio relative to QR width [0.10-0.35].",
    )
    p_generate.set_defaults(func=cmd_generate)

    p_cfg = sub.add_parser("from-config", help="Generate a single QR image from config.json.")
    p_cfg.add_argument("--config", default="config.json", help="Config file path.")
    p_cfg.add_argument("--output", default="", help="Optional output override.")
    p_cfg.add_argument("--logo", default="", help="Center logo image path (PNG/JPG).")
    p_cfg.add_argument(
        "--logo-scale",
        type=float,
        default=0.2,
        help="Center logo size ratio relative to QR width [0.10-0.35].",
    )
    p_cfg.set_defaults(func=cmd_from_config)

    p_batch = sub.add_parser("batch", help="Generate multiple QR images from config batch_profiles.")
    p_batch.add_argument("--config", default="config.json", help="Config file path.")
    p_batch.set_defaults(func=cmd_batch)

    p_verify = sub.add_parser("verify", help="Verify URL accessibility and QR decode consistency.")
    p_verify.add_argument("--url", required=True, help="Expected full URL encoded in QR.")
    p_verify.add_argument("--qrcode", required=True, help="QR image path.")
    p_verify.add_argument("--timeout", type=int, default=8, help="HTTP timeout seconds.")
    p_verify.set_defaults(func=cmd_verify)

    p_perf = sub.add_parser("perf", help="Run local performance baseline for QR generation.")
    p_perf.add_argument("--base-url", default="http://localhost:8090", help="Base URL for about page.")
    p_perf.add_argument("--output-dir", default="output/perf", help="Output directory for generated files.")
    p_perf.add_argument("--runs", type=int, default=5, help="Number of generation runs.")
    p_perf.add_argument("--size", type=int, default=10, help="QR box size [1-40].")
    p_perf.add_argument("--border", type=int, default=2, help="QR border width (>=0).")
    p_perf.set_defaults(func=cmd_perf)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, ConfigError, FileNotFoundError, PermissionError) as exc:
        _emit({"ok": False, "error": str(exc)})
        return 2
    except Exception as exc:  # pragma: no cover
        _emit({"ok": False, "error": f"unexpected error: {exc}"})
        return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
