#!/usr/bin/env python3
"""Generate one QR image from config.json defaults."""

from __future__ import annotations

from pathlib import Path

from generate_qrcode import build_about_page_url, generate_about_us_qrcode
from qrcode_config import parse_runtime_config


def main(config_path: str = "config.json") -> Path:
    runtime = parse_runtime_config(config_path)
    style = runtime.default_style
    output = generate_about_us_qrcode(
        base_url=runtime.base_url,
        output_path=style.output_path,
        size=style.size,
        border=style.border,
        fill_color=style.fill_color,
        back_color=style.back_color,
        page_path=runtime.page_path,
    )
    print(f"配置文件: {runtime.config_path.resolve()}")
    print(f"目标 URL: {build_about_page_url(runtime.base_url, runtime.page_path)}")
    print(f"二维码文件: {Path(output).resolve()}")
    return output


if __name__ == "__main__":
    main()

