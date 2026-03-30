#!/usr/bin/env python3
"""Configuration helpers for the About-Us QR code toolchain."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generate_qrcode import DEFAULT_PAGE_PATH, normalize_page_path, validate_http_url


class ConfigError(ValueError):
    """Raised when config.json is invalid."""


@dataclass(frozen=True)
class QRStyleConfig:
    size: int = 10
    border: int = 2
    fill_color: str = "black"
    back_color: str = "white"
    output_path: str = "output/about_us_qrcode.png"

    def merged(self, overrides: dict[str, Any]) -> "QRStyleConfig":
        payload = {
            "size": self.size,
            "border": self.border,
            "fill_color": self.fill_color,
            "back_color": self.back_color,
            "output_path": self.output_path,
        }
        payload.update({k: v for k, v in overrides.items() if v is not None})
        return QRStyleConfig(
            size=int(payload["size"]),
            border=int(payload["border"]),
            fill_color=str(payload["fill_color"]),
            back_color=str(payload["back_color"]),
            output_path=str(payload["output_path"]),
        )


@dataclass(frozen=True)
class GitHubPagesConfig:
    username: str = ""
    repository: str = ""
    page_path: str = DEFAULT_PAGE_PATH
    custom_domain: str = ""


@dataclass(frozen=True)
class QRCodeRuntimeConfig:
    base_url: str
    page_path: str
    default_style: QRStyleConfig
    batch_profiles: list[dict[str, Any]]
    config_path: Path


def _require_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"配置项 '{field_name}' 必须是对象")
    return value


def load_config_file(config_path: str | Path = "config.json") -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"配置文件不存在: {path}")
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"无法读取配置文件: {path}") from exc
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"配置文件 JSON 格式错误: {path} (line {exc.lineno})") from exc
    if not isinstance(payload, dict):
        raise ConfigError("配置文件根节点必须是 JSON 对象")
    return payload


def build_github_pages_base_url(github_cfg: GitHubPagesConfig) -> str:
    custom_domain = github_cfg.custom_domain.strip()
    if custom_domain:
        if custom_domain.startswith("http://") or custom_domain.startswith("https://"):
            domain_url = custom_domain
        else:
            domain_url = f"https://{custom_domain}"
        return validate_http_url(domain_url).rstrip("/")

    username = github_cfg.username.strip()
    repository = github_cfg.repository.strip()
    if not username or not repository:
        raise ConfigError("github_pages.username 与 github_pages.repository 不能为空")
    return f"https://{username}.github.io/{repository}".rstrip("/")


def parse_runtime_config(config_path: str | Path = "config.json") -> QRCodeRuntimeConfig:
    raw = load_config_file(config_path=config_path)

    github_pages_raw = _require_dict(raw.get("github_pages", {}), "github_pages")
    github_cfg = GitHubPagesConfig(
        username=str(github_pages_raw.get("username", "")).strip(),
        repository=str(github_pages_raw.get("repository", "")).strip(),
        page_path=normalize_page_path(str(github_pages_raw.get("page_path", DEFAULT_PAGE_PATH))),
        custom_domain=str(github_pages_raw.get("custom_domain", "")).strip(),
    )
    base_url = build_github_pages_base_url(github_cfg=github_cfg)

    style_raw = _require_dict(raw.get("qrcode_default", {}), "qrcode_default")
    default_style = QRStyleConfig(
        size=int(style_raw.get("size", 10)),
        border=int(style_raw.get("border", 2)),
        fill_color=str(style_raw.get("fill_color", "black")),
        back_color=str(style_raw.get("back_color", "white")),
        output_path=str(style_raw.get("output_path", "output/about_us_qrcode.png")),
    )

    batch_profiles = raw.get("batch_profiles", [])
    if batch_profiles is None:
        batch_profiles = []
    if not isinstance(batch_profiles, list):
        raise ConfigError("配置项 'batch_profiles' 必须是数组")
    normalized_profiles: list[dict[str, Any]] = []
    for idx, profile in enumerate(batch_profiles):
        if not isinstance(profile, dict):
            raise ConfigError(f"batch_profiles[{idx}] 必须是对象")
        normalized_profiles.append(profile)

    return QRCodeRuntimeConfig(
        base_url=base_url,
        page_path=github_cfg.page_path,
        default_style=default_style,
        batch_profiles=normalized_profiles,
        config_path=Path(config_path),
    )

