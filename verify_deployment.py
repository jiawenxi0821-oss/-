#!/usr/bin/env python3
"""Deployment and QR verification utilities."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests


def test_url_accessibility(url: str, timeout_sec: int = 8) -> dict[str, Any]:
    """Check URL availability and response timing."""
    started = time.perf_counter()
    try:
        resp = requests.get(url, timeout=timeout_sec)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "ok": resp.status_code == 200,
            "status_code": resp.status_code,
            "elapsed_ms": elapsed_ms,
            "error": "",
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "ok": False,
            "status_code": 0,
            "elapsed_ms": elapsed_ms,
            "error": str(exc),
        }


def _decode_with_pyzbar(image_path: Path) -> tuple[str | None, str]:
    try:
        from PIL import Image
        import pyzbar.pyzbar as pyzbar
    except Exception as exc:
        return None, f"pyzbar unavailable: {exc}"

    try:
        img = Image.open(image_path)
        decoded = pyzbar.decode(img)
        if not decoded:
            return None, "pyzbar did not decode any QR payload"
        return decoded[0].data.decode("utf-8"), ""
    except Exception as exc:
        return None, f"pyzbar decode failed: {exc}"


def _decode_with_opencv(image_path: Path) -> tuple[str | None, str]:
    try:
        import cv2
    except Exception as exc:
        return None, f"opencv unavailable: {exc}"

    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return None, "opencv failed to load image"
        detector = cv2.QRCodeDetector()
        decoded_text, _, _ = detector.detectAndDecode(img)
        if not decoded_text:
            return None, "opencv did not decode any QR payload"
        return decoded_text, ""
    except Exception as exc:
        return None, f"opencv decode failed: {exc}"


def decode_qrcode_payload(image_path: str | Path) -> str:
    """Decode QR payload using available backends."""
    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"二维码文件不存在: {image_file}")

    pyzbar_value, pyzbar_err = _decode_with_pyzbar(image_file)
    if pyzbar_value:
        return pyzbar_value

    opencv_value, opencv_err = _decode_with_opencv(image_file)
    if opencv_value:
        return opencv_value

    raise RuntimeError(
        "二维码解码失败。"
        f" pyzbar={pyzbar_err or 'n/a'};"
        f" opencv={opencv_err or 'n/a'}"
    )


def verify_qrcode(expected_url: str, qrcode_path: str | Path) -> dict[str, Any]:
    """Verify QR file can be decoded and matches expected URL exactly."""
    try:
        decoded_url = decode_qrcode_payload(qrcode_path)
    except Exception as exc:
        return {
            "ok": False,
            "decoded_url": "",
            "expected_url": expected_url,
            "error": str(exc),
        }

    return {
        "ok": decoded_url == expected_url,
        "decoded_url": decoded_url,
        "expected_url": expected_url,
        "error": "" if decoded_url == expected_url else "二维码 URL 与预期不一致",
    }


def verify_deployment(
    *,
    expected_url: str,
    qrcode_path: str | Path,
    timeout_sec: int = 8,
) -> dict[str, Any]:
    """End-to-end verification: URL reachable + QR decodes to expected URL."""
    url_result = test_url_accessibility(url=expected_url, timeout_sec=timeout_sec)
    qr_result = verify_qrcode(expected_url=expected_url, qrcode_path=qrcode_path)
    return {
        "ok": url_result["ok"] and qr_result["ok"],
        "url_check": url_result,
        "qrcode_check": qr_result,
    }

