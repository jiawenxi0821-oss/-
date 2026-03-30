#!/usr/bin/env python3
"""Tests for config, batch generation and verification helpers."""

from __future__ import annotations

import json
from pathlib import Path

from batch_generate import generate_batch_qrcodes
from qrcode_config import ConfigError, parse_runtime_config
from verify_deployment import verify_qrcode, verify_deployment


def test_parse_runtime_config_success(tmp_path: Path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "github_pages": {
                    "username": "demo-user",
                    "repository": "demo-repo",
                    "page_path": "/about.html",
                    "custom_domain": "",
                },
                "qrcode_default": {
                    "size": 10,
                    "border": 2,
                    "fill_color": "black",
                    "back_color": "white",
                    "output_path": str(tmp_path / "single.png"),
                },
                "batch_profiles": [{"name": "poster", "output_path": str(tmp_path / "poster.png")}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    runtime = parse_runtime_config(config_path)
    assert runtime.base_url == "https://demo-user.github.io/demo-repo"
    assert runtime.page_path == "/about.html"
    assert runtime.default_style.output_path.endswith("single.png")


def test_parse_runtime_config_invalid_json(tmp_path: Path):
    broken = tmp_path / "broken.json"
    broken.write_text("{ bad json", encoding="utf-8")
    try:
        parse_runtime_config(broken)
        assert False, "Expected ConfigError"
    except ConfigError as exc:
        assert "JSON" in str(exc)


def test_batch_generation_failure_isolated(tmp_path: Path):
    summary = generate_batch_qrcodes(
        base_url="https://example.com",
        page_path="/about.html",
        default_style=parse_runtime_config("config.example.json").default_style.merged(
            {"output_path": str(tmp_path / "default.png")}
        ),
        profiles=[
            {"name": "ok", "output_path": str(tmp_path / "ok.png"), "size": 8},
            {"name": "bad", "output_path": str(tmp_path / "bad.png"), "size": 0},
        ],
    )
    assert summary["total"] == 2
    assert summary["success"] == 1
    assert summary["failed"] == 1
    failed_row = [row for row in summary["results"] if not row["success"]][0]
    assert failed_row["name"] == "bad"


def test_verify_qrcode_mismatch(monkeypatch):
    monkeypatch.setattr("verify_deployment.decode_qrcode_payload", lambda _path: "https://a.com/about.html")
    result = verify_qrcode(expected_url="https://b.com/about.html", qrcode_path="mock.png")
    assert result["ok"] is False
    assert "不一致" in result["error"]


def test_verify_deployment_aggregates(monkeypatch):
    monkeypatch.setattr(
        "verify_deployment.test_url_accessibility",
        lambda **kwargs: {"ok": True, "status_code": 200, "elapsed_ms": 12.0, "error": ""},
    )
    monkeypatch.setattr(
        "verify_deployment.verify_qrcode",
        lambda **kwargs: {
            "ok": True,
            "decoded_url": kwargs["expected_url"],
            "expected_url": kwargs["expected_url"],
            "error": "",
        },
    )
    result = verify_deployment(expected_url="https://demo.com/about.html", qrcode_path="x.png")
    assert result["ok"] is True
    assert result["url_check"]["status_code"] == 200

