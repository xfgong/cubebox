# WeCom file transfer implementation plan

**Goal:** WeCom inbound images/files/videos become CubePlex attachments, and
outbound artifacts / `present_file` blobs become native WeCom media messages.

**Architecture:** Reuse the shared IM attachment and artifact pipelines.
WeCom-specific work is parse → opaque handle, HTTP+AES download, and a
gateway three-step upload plus proactive `aibot_send_msg`. The agent runtime
does not change.

**Tech stack:** Existing `aiohttp` WebSocket gateway, `httpx` download,
`cryptography` AES-256-CBC, pytest.

**Spec:** `docs/dev/specs/2026-09-07-wecom-file-transfer-design.md`

## Unit 1 — Media helpers (handle, decrypt, outbound type)

**Files:**

- Create `backend/cubeplex/im/wecom/media.py`
- Create `backend/tests/unit/im/wecom/test_media.py`

**Interfaces:**

- `encode_media_handle(url, aeskey) -> str` / `decode_media_handle(handle) -> (url, aeskey)`
- `decrypt_wecom_media(ciphertext, aeskey) -> bytes`
- `outbound_media_type(filename, mime, size) -> "image" | "file"`

**Core logic:** URL-safe Base64 with restored padding; IV = key[:16];
manual PKCS#7 (pad 1–32). Image type only when size ≤ 10 MiB and the name/mime
is an image. Empty url/key is an error, not a silent raw-bytes passthrough.

**Tests:** round-trip encrypt/decrypt; url-safe unpadded key; invalid pad
raises; image vs file type selection.

## Unit 2 — Inbound parse

**Files:**

- Modify `backend/cubeplex/im/wecom/connector.py`
- Modify `backend/tests/unit/im/wecom/test_connector.py`

**Interfaces:** `parse_inbound` returns `InboundEvent.attachments` and no
longer requires text when attachments exist.

**Core logic:** Collect image/file/video bodies and mixed image items. Keep
group mention-strip; after strip, keep the event if attachments remain.
Bot-echo and missing msgid/req_id/sender still drop. Quote media is not
turned into refs.

**Tests:** image/file/video/mixed refs; media-only DM kept; mention-only group
image kept; previous image-only drop case updated; quote-image without text
still dropped unless quote text/voice exists.

## Unit 3 — Download into `download_for`

**Files:**

- Modify `backend/cubeplex/im/inbound_attachments.py`
- Modify `backend/tests/unit/im/wecom/test_media.py` (or a dedicated download
  test) with `httpx` mocked at the HTTP boundary.

**Interfaces:** `download_for("wecom", client, ref, message_id=...)` ignores
`client`/`message_id` (URL is in the handle). `_client_for_download` stays
`None` for WeCom.

**Core logic:** Decode handle → size-capped GET → decrypt. HTTP/decrypt
failures become `DownloadError` so the worker notes-and-skips.

**Tests:** decrypts ciphertext; missing aeskey fails; HTML/error GET fails.

## Unit 4 — Gateway upload + connector send

**Files:**

- Modify `backend/cubeplex/im/wecom/gateway.py`
- Modify `backend/cubeplex/im/wecom/connector.py`
- Modify `backend/cubeplex/im/artifact_delivery.py`
- Modify `backend/tests/unit/im/wecom/test_gateway.py`
- Modify `backend/tests/unit/im/wecom/test_connector.py`
- Modify `backend/tests/unit/test_artifact_delivery.py`

**Interfaces:**

- `WecomGateway.upload_media(*, data, filename, media_type) -> str` (`media_id`)
- `WecomConnector.send_file` / `send_image` → upload then
  `send_proactive(chat_id, {msgtype, {media_id}})`

**Core logic:** Sequential 512 KiB chunks, max 100. `send_file` never uses
the inbound `req_id`. Failure returns `False`. `outbound_size_cap("wecom")`
= 20 MiB.

**Tests:** init/chunk/finish order and `media_id`; chunk failure does not
finish; `send_file` proactive body; missing chat_id/`gateway` returns False;
size cap assertion.

## Unit 5 — Docs

**Files:**

- `docs/site/docs/guides/im/wecom.md`
- `docs/site/i18n/zh-Hans/.../guides/im/wecom.md`
- `docs/site/docs/guides/im/overview.md` (and zh-Hans overview)

**Core logic:** State that native image/file transfer is supported; keep HITL
cards and personal WeChat as limits. Mention the five-minute inbound URL TTL
and DM-only platform inbound for standalone image/file/video.
