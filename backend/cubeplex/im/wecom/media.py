"""WeCom AI Bot media handle encoding, AES decrypt, and outbound type selection."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"})
_IMAGE_MAX_BYTES = 10 * 1024 * 1024


class WecomMediaError(ValueError):
    """Handle parse or AES decrypt failed — callers map this to DownloadError."""


def encode_media_handle(url: str, aeskey: str) -> str:
    """Pack the short-lived download URL and aeskey into an opaque queue handle."""
    return json.dumps({"url": url, "aeskey": aeskey}, separators=(",", ":"))


def decode_media_handle(handle: str) -> tuple[str, str]:
    try:
        payload: Any = json.loads(handle)
    except (TypeError, ValueError) as exc:
        raise WecomMediaError("WeCom media handle is not JSON") from exc
    if not isinstance(payload, dict):
        raise WecomMediaError("WeCom media handle is not an object")
    url = str(payload.get("url") or "").strip()
    aeskey = str(payload.get("aeskey") or "").strip()
    if not url:
        raise WecomMediaError("WeCom media handle is missing url")
    return url, aeskey


def decode_aes_key(aeskey: str) -> bytes:
    """Decode a WeCom aeskey, including URL-safe unpadded Base64."""
    text = aeskey.strip()
    if not text:
        raise WecomMediaError("empty aeskey")
    padded = text + "=" * ((4 - len(text) % 4) % 4)
    normalized = padded.replace("+", "-").replace("/", "_")
    try:
        key = base64.urlsafe_b64decode(normalized)
    except (ValueError, TypeError) as exc:
        raise WecomMediaError("invalid aeskey") from exc
    if len(key) != 32:
        raise WecomMediaError(f"aeskey decoded to {len(key)} bytes, want 32")
    return key


def decrypt_wecom_media(ciphertext: bytes, aeskey: str) -> bytes:
    """AES-256-CBC decrypt with PKCS#7 unpadding (pad length 1–32)."""
    if not ciphertext:
        raise WecomMediaError("empty ciphertext")
    key = decode_aes_key(aeskey)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(key[:16])).decryptor()
    try:
        padded = decryptor.update(ciphertext) + decryptor.finalize()
    except Exception as exc:
        raise WecomMediaError("AES decrypt failed") from exc
    if not padded:
        raise WecomMediaError("AES decrypt produced no data")
    pad_len = padded[-1]
    if pad_len < 1 or pad_len > 32 or pad_len > len(padded):
        raise WecomMediaError(f"invalid PKCS#7 padding value: {pad_len}")
    if any(byte != pad_len for byte in padded[-pad_len:]):
        raise WecomMediaError("invalid PKCS#7 padding bytes")
    return padded[:-pad_len]


def outbound_media_type(filename: str, mime: str | None, size: int) -> str:
    """Pick WeCom upload type. Images over 10 MiB downgrade to file."""
    if size > _IMAGE_MAX_BYTES:
        return "file"
    declared = (mime or "").split(";", 1)[0].strip().lower()
    if declared.startswith("image/"):
        return "image"
    if Path(filename).suffix.lower() in _IMAGE_EXTS:
        return "image"
    return "file"
