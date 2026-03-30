#!/usr/bin/env python3
"""QR code generation helpers for the About page."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

DEFAULT_PAGE_PATH = "/about.html"
DEFAULT_LOGO_PATH = "ui copy/logo.png"


def normalize_page_path(page_path: str = DEFAULT_PAGE_PATH) -> str:
    """Normalize page path and ensure it starts with '/'"""
    if page_path is None or not str(page_path).strip():
        raise ValueError("page_path 不能为空")
    path = str(page_path).strip()
    if not path.startswith("/"):
        path = "/" + path
    return path


def validate_http_url(url: str) -> str:
    """Validate URL must be http/https and include hostname."""
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
    """Build complete about-page URL from base URL and page path."""
    normalized_base = validate_http_url(base_url).rstrip("/")
    normalized_path = normalize_page_path(page_path)
    return normalized_base + normalized_path


def _validate_qrcode_params(size: int, border: int) -> None:
    if not isinstance(size, int) or not (1 <= size <= 40):
        raise ValueError("size 必须在 1-40 之间")
    if not isinstance(border, int) or border < 0:
        raise ValueError("border 必须为非负整数")


def _validate_logo_scale(logo_scale: float) -> None:
    if not isinstance(logo_scale, (float, int)):
        raise ValueError("logo_scale 必须是数字")
    if not 0.10 <= float(logo_scale) <= 0.35:
        raise ValueError("logo_scale 必须在 0.10 - 0.35 之间")


def _overlay_logo_at_center(qr_img, logo_path: str, logo_scale: float = 0.2):
    """Overlay a logo at the center of QR code while preserving scan reliability."""
    from PIL import Image, ImageDraw

    logo_file = Path(str(logo_path)).expanduser()
    if not logo_file.exists():
        raise FileNotFoundError(f"Logo 文件不存在: {logo_file}")

    _validate_logo_scale(logo_scale)

    qr_rgba = qr_img.convert("RGBA")
    qr_w, qr_h = qr_rgba.size
    target_logo_size = max(24, int(min(qr_w, qr_h) * float(logo_scale)))

    resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS

    with Image.open(str(logo_file)) as logo_source:
        logo_rgba = logo_source.convert("RGBA")
        logo_rgba.thumbnail((target_logo_size, target_logo_size), resample=resample)

    pad = max(4, logo_rgba.size[0] // 8)
    badge_w = logo_rgba.size[0] + pad * 2
    badge_h = logo_rgba.size[1] + pad * 2

    # Add a rounded white badge behind logo for contrast.
    mask = Image.new("L", (badge_w, badge_h), 0)
    draw = ImageDraw.Draw(mask)
    radius = max(8, min(badge_w, badge_h) // 6)
    draw.rounded_rectangle((0, 0, badge_w, badge_h), radius=radius, fill=255)
    badge = Image.new("RGBA", (badge_w, badge_h), (255, 255, 255, 255))
    badge.putalpha(mask)

    logo_x = (badge_w - logo_rgba.size[0]) // 2
    logo_y = (badge_h - logo_rgba.size[1]) // 2
    badge.paste(logo_rgba, (logo_x, logo_y), logo_rgba)

    center_x = (qr_w - badge_w) // 2
    center_y = (qr_h - badge_h) // 2
    qr_rgba.paste(badge, (center_x, center_y), badge)
    return qr_rgba


def generate_qrcode_for_url(
    full_url: str,
    output_path: str = "about_us_qrcode.png",
    size: int = 10,
    border: int = 2,
    fill_color: str = "black",
    back_color: str = "white",
    logo_path: str | None = None,
    logo_scale: float = 0.2,
    quiet: bool = False,
) -> Path:
    """Generate a QR image for a complete URL."""
    validated_url = validate_http_url(full_url)
    _validate_qrcode_params(size=size, border=border)

    use_logo = bool(str(logo_path).strip()) if logo_path is not None else False
    if use_logo:
        _validate_logo_scale(logo_scale)

    import qrcode

    qr = qrcode.QRCode(
        version=1,
        error_correction=(
            qrcode.constants.ERROR_CORRECT_H if use_logo else qrcode.constants.ERROR_CORRECT_L
        ),
        box_size=size,
        border=border,
    )
    qr.add_data(validated_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGBA")
    if use_logo:
        img = _overlay_logo_at_center(
            qr_img=img,
            logo_path=str(logo_path),
            logo_scale=logo_scale,
        )

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
    logo_path: str | None = None,
    logo_scale: float = 0.2,
) -> Path:
    """Generate QR image for the About page URL."""
    full_url = build_about_page_url(base_url=base_url, page_path=page_path)

    resolved_logo = logo_path
    if resolved_logo is None:
        auto_logo = Path(DEFAULT_LOGO_PATH)
        if auto_logo.exists():
            resolved_logo = str(auto_logo)

    return generate_qrcode_for_url(
        full_url=full_url,
        output_path=output_path,
        size=size,
        border=border,
        fill_color=fill_color,
        back_color=back_color,
        logo_path=resolved_logo,
        logo_scale=logo_scale,
    )


if __name__ == "__main__":
    qr_path = generate_about_us_qrcode(base_url="http://localhost:8080")
    print(f"✅ 二维码生成成功: {qr_path}")
