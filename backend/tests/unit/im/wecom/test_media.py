from __future__ import annotations

import base64
import os
from typing import Any

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from cubeplex.im.inbound_attachments import DownloadError, download_for
from cubeplex.im.types import InboundAttachmentRef
from cubeplex.im.wecom.media import (
    WecomMediaError,
    decode_media_handle,
    decrypt_wecom_media,
    encode_media_handle,
    outbound_media_type,
)


def _encrypt(plaintext: bytes, aeskey: str) -> bytes:
    padded_key = aeskey + "=" * ((4 - len(aeskey) % 4) % 4)
    key = base64.urlsafe_b64decode(padded_key.replace("+", "-").replace("/", "_"))
    pad_len = 32 - (len(plaintext) % 32)
    padded = plaintext + bytes([pad_len] * pad_len)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(key[:16])).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def test_handle_round_trip_keeps_url_and_aeskey() -> None:
    handle = encode_media_handle("https://work.weixin.qq.com/a", "abc")
    assert decode_media_handle(handle) == ("https://work.weixin.qq.com/a", "abc")


def test_decode_handle_rejects_missing_url() -> None:
    with pytest.raises(WecomMediaError, match="url"):
        decode_media_handle('{"aeskey":"x"}')


def test_decrypt_accepts_urlsafe_unpadded_aeskey() -> None:
    key = os.urandom(32)
    aeskey = base64.urlsafe_b64encode(key).decode().rstrip("=")
    plaintext = b"wecom-attachment-bytes"
    assert decrypt_wecom_media(_encrypt(plaintext, aeskey), aeskey) == plaintext


def test_decrypt_rejects_ciphertext_as_plaintext() -> None:
    key = os.urandom(32)
    aeskey = base64.urlsafe_b64encode(key).decode()
    with pytest.raises(WecomMediaError):
        decrypt_wecom_media(b"not-really-ciphertext-16!!", aeskey)


@pytest.mark.parametrize(
    ("filename", "mime", "size", "expected"),
    [
        ("shot.png", None, 100, "image"),
        ("shot.bin", "image/jpeg", 100, "image"),
        ("shot.png", "image/png", 10 * 1024 * 1024 + 1, "file"),
        ("report.pdf", "application/pdf", 100, "file"),
    ],
)
def test_outbound_media_type(filename: str, mime: str | None, size: int, expected: str) -> None:
    assert outbound_media_type(filename, mime, size) == expected


@pytest.mark.asyncio
async def test_download_for_wecom_decrypts_ciphertext(monkeypatch: pytest.MonkeyPatch) -> None:
    key = os.urandom(32)
    aeskey = base64.urlsafe_b64encode(key).decode().rstrip("=")
    plaintext = b"hello-wecom-file"
    ciphertext = _encrypt(plaintext, aeskey)
    ref = InboundAttachmentRef(
        kind="file",
        filename="note.txt",
        mime="text/plain",
        handle=encode_media_handle("https://work.weixin.qq.com/media/x", aeskey),
    )

    async def fake_download(
        url: str, headers: dict[str, str] | None = None, **kwargs: Any
    ) -> bytes:
        del headers, kwargs
        assert url.startswith("https://work.weixin.qq.com/")
        return ciphertext

    monkeypatch.setattr("cubeplex.im.inbound_attachments._download_url", fake_download)
    assert await download_for("wecom", None, ref, message_id=None) == plaintext


@pytest.mark.asyncio
async def test_download_for_wecom_missing_aeskey_is_download_error() -> None:
    ref = InboundAttachmentRef(
        kind="image",
        filename="image",
        mime=None,
        handle=encode_media_handle("https://work.weixin.qq.com/media/x", ""),
    )
    with pytest.raises(DownloadError):
        await download_for("wecom", None, ref, message_id=None)
