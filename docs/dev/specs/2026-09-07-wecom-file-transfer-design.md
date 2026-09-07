# WeCom IM file transfer

## Goal

Let WeCom users send images and files to the CubePlex agent, and let the agent
deliver `present_file` / `save_artifact` results as native WeCom image or file
messages instead of HTTP share links.

## Context

WeCom v1 is text-first. `WecomConnector.parse_inbound` drops media-only
callbacks, and `send_file` / `send_image` always return `False`. Feishu, Slack,
Discord, and DingTalk already use the shared inbound attachment pipeline
(`InboundAttachmentRef` → worker download → `AttachmentService.upload` →
`start_run`) and the outbound artifact dispatcher (`send_file` at run
terminal, share-link fallback).

The WeCom AI Bot protocol already supports this:

- Inbound `image` / `file` / `video` (and images inside `mixed`) carry a
  five-minute download URL plus an `aeskey`. Bytes on the wire are AES-256-CBC
  ciphertext.
- Outbound media uses a three-step WebSocket upload
  (`aibot_upload_media_init` → `aibot_upload_media_chunk` →
  `aibot_upload_media_finish`) that returns a `media_id`, then
  `aibot_send_msg` / `aibot_respond_msg` with `{msgtype, media_id}`.

Official WeCom docs say inbound image/file/voice/video callbacks are
direct-message only. Group mixed messages can still include image items. This
change parses whatever the callback actually contains; it does not invent a
group download API.

## Approaches considered

### 1. Plug WeCom into the existing IM file pipeline — chosen

Parse WeCom media into `InboundAttachmentRef`, download/decrypt in
`download_for("wecom", ...)`, and implement `send_file` / `send_image` on the
bound connector. No new queue columns, routes, or agent-path changes.

Keep the protocol inside `WecomGateway`, matching v1. Adding
`wecom-aibot-sdk` would duplicate the socket we already own and fight the
single-connection lease.

### 2. Depend on an official AI Bot SDK

Faster media helpers, but a second WebSocket client next to `WecomGateway`.
Rejected.

### 3. Outbound-only, keep inbound dropped

Smaller, but the common WeCom path is "send a screenshot / PDF to the bot".
Rejected as the first slice.

## Design

### Inbound

`parse_inbound` keeps a callback when there is text **or** at least one
downloadable media ref. Voice stays transcription-only (no audio download).
Quoted media is not fetched; quote text/voice fallback stays as in v1.

Refs:

| `msgtype` | `kind` | filename |
|---|---|---|
| `image` | `image` | `image` (bytes are sniffed later) |
| `file` | `file` | `file.name` / `file.filename` if present, else `file` |
| `video` | `video` | `video` |
| `mixed` image items | `image` | `image` |

`handle` is a compact JSON object `{"url","aeskey"}` so both values survive
queue serialization. The URL is a secret-equivalent (short-lived, encrypted
object); logs must not print the handle.

`download_for` for WeCom:

1. Parse the handle.
2. HTTP GET the URL (existing size-capped stream helper).
3. AES-256-CBC decrypt when `aeskey` is present: key is URL-safe Base64
   (padding restored), IV is `key[:16]`, PKCS#7 unpadding with a 1–32 byte
   pad (WeCom uses a 32-byte pad block). Missing/invalid keys raise
   `DownloadError`.
4. Existing MIME allowlist, size cap, and `[附件 … 已忽略]` notes apply.

Download runs in the worker after claim, same as every other platform. WeCom
URLs expire in five minutes; a queue delay past that TTL skips the file with
the existing note rather than failing the run.

### Outbound

`WecomGateway.upload_media(data, filename, media_type) -> media_id`:

- `type` is `image` or `file` (no voice/video send in this change).
- Raw chunk size 512 KiB, max 100 chunks (~50 MiB protocol ceiling).
- MD5 of the plaintext bytes, hex.
- Sequential chunks (WeCom errors under high chunk concurrency).
- Each step uses the existing request/ACK waiter.

`send_file` / `send_image` then send `{msgtype, {media_id}}` with
`aibot_send_msg` to the bound `chat_id`. Terminal file delivery happens
**after** the stream `finish=true` frame, so reusing the inbound `req_id`
would race the stream waiter or hit an expired callback. Proactive send is
the only safe path. Upload or send failure returns `False` and the dispatcher
falls back to a share link.

Native type: `image` when the file is an image **and** ≤ 10 MiB; otherwise
`file`. Platform cap in `outbound_size_cap("wecom")` is 20 MiB (Hermes/WeCom
native file ceiling). Larger artifacts skip upload and use the share link.

`upload_image` stays `None`. WeCom has no Feishu-style inline `image_key`,
and `_platform.py` already sets `supports_inline_image=False`.

### Docs

Update the WeCom guide and IM overview: native image/file send and receive
are in; HITL cards and personal WeChat stay out.

## Out of scope

- WeCom template cards / in-chat AskUser or sandbox-confirm buttons.
- Personal WeChat and self-built application callbacks.
- Outbound voice or video messages.
- Downloading quoted media or inbound voice bytes.
- Changing attachment MIME allowlists, sandbox hydration, or web upload.
- Adding an official WeCom SDK dependency.

## Success criteria

- A linked member's WeCom image, file, video, or mixed image+text message
  produces attachment ids on `start_run`, same as a web upload.
- A media-only DM is ingested instead of dropped.
- AES decryption uses the callback `aeskey`; ciphertext must not be stored
  as the attachment.
- `present_file` images and file-type artifacts arrive as native WeCom
  messages when under the size cap; oversize or upload failure still sends
  the existing share link.
- Voice callbacks remain transcription-only.
- Existing WeCom text, stream, reconnect, and identity-link behavior is
  unchanged.
