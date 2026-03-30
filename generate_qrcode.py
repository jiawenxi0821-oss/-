#!/usr/bin/env python3
"""
关于我们页面二维码生成脚本
生成包含 about.html 完整 URL 的二维码图片
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

DEFAULT_PAGE_PATH = "/about.html"


def normalize_page_path(page_path: str = DEFAULT_PAGE_PATH) -> str:
    """标准化页面路径，确保以 `/` 开头。"""
    if page_path is None or not str(page_path).strip():
        raise ValueError("page_path 不能为空")
    path = str(page_path).strip()
    if not path.startswith("/"):
        path = "/" + path
    return path


def validate_http_url(url: str) -> str:
    """校验 URL 必须是 http/https 且包含域名。"""
    if url is None or not str(url).strip():
        raise ValueError("URL 不能为空")

    cleaned = str(url).strip()
    if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
        raise ValueError("URL 格式无效，必须以 http:// 或 https:// 开头")

    parsed = urlparse(cleaned)
    if not parsed.netloc:
        raise ValueError("URL 格式无效，必须包含域名")
    return cleaned


def build_about_page_url(base_url: str, page_path: str = DEFAULT_PAGE_PATH) -> str:
    """由 base_url 构建完整 about 页面 URL。"""
    normalized_base = validate_http_url(base_url).rstrip("/")
    normalized_path = normalize_page_path(page_path)
    return normalized_base + normalized_path


def _validate_qrcode_params(size: int, border: int) -> None:
    if not isinstance(size, int) or not (1 <= size <= 40):
        raise ValueError("size 必须在 1-40 之间")
    if not isinstance(border, int) or border < 0:
        raise ValueError("border 必须为非负整数")


def generate_qrcode_for_url(
    full_url: str,
    output_path: str = "about_us_qrcode.png",
    size: int = 10,
    border: int = 2,
    fill_color: str = "black",
    back_color: str = "white",
    quiet: bool = False,
) -> Path:
    """
    为任意完整 URL 生成二维码图片。
    """
    validated_url = validate_http_url(full_url)
    _validate_qrcode_params(size=size, border=border)

    import qrcode

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(validated_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    output_file = Path(output_path)
    output_dir = output_file.parent
    try:
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(f"无法创建输出目录 '{output_dir}': 权限不足") from exc
    except OSError as exc:
        raise PermissionError(f"无法创建输出目录 '{output_dir}': {exc}") from exc

    try:
        img.save(str(output_file))
    except PermissionError as exc:
        raise PermissionError(f"无法写入文件 '{output_file}': 权限不足") from exc
    except OSError as exc:
        raise PermissionError(f"无法写入文件 '{output_file}': {exc}") from exc

    if not output_file.exists() or output_file.stat().st_size == 0:
        raise RuntimeError(f"二维码文件生成失败: {output_file}")

    if not quiet:
        print(f"二维码已生成: {output_file.absolute()}")
        print(f"扫描后访问: {validated_url}")
    return output_file


def generate_about_us_qrcode(
    base_url: str,
    output_path: str = "about_us_qrcode.png",
    size: int = 10,
    border: int = 2,
    fill_color: str = "black",
    back_color: str = "white",
    page_path: str = DEFAULT_PAGE_PATH,
) -> Path:
    """
    生成关于我们页面的二维码图片

    Args:
        base_url: 网站基础 URL（如 http://localhost:8080）
        output_path: 输出文件路径
        size: 二维码大小（1-40）
        border: 边框宽度
        fill_color: 前景色
        back_color: 背景色
        page_path: 页面路径（默认 /about.html）

    Returns:
        Path: 生成的二维码文件路径

    Raises:
        ValueError: 当输入参数无效时
        PermissionError: 当文件系统无写入权限时
    """
    full_url = build_about_page_url(base_url=base_url, page_path=page_path)
    return generate_qrcode_for_url(
        full_url=full_url,
        output_path=output_path,
        size=size,
        border=border,
        fill_color=fill_color,
        back_color=back_color,
    )


if __name__ == "__main__":
    qr_path = generate_about_us_qrcode(base_url="http://localhost:8080")
    print(f"✓ 二维码生成成功: {qr_path}")
