<p align="center">
  <img src="icon.png" alt="mailprobe" width="128">
</p>

# mailprobe

[![CI](https://github.com/frederikb96/mailprobe/actions/workflows/ci.yaml/badge.svg)](https://github.com/frederikb96/mailprobe/actions/workflows/ci.yaml)
[![Release](https://img.shields.io/github/v/release/frederikb96/mailprobe)](https://github.com/frederikb96/mailprobe/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

IMAP email MCP server with hybrid full-text body search.

Most IMAP servers (including Posteo, many self-hosted setups) don't support server-side full-text body search. Existing email MCP servers silently return empty results when searching email bodies on these servers. mailprobe solves this with a hybrid approach: fast server-side filtering for metadata (dates, sender, subject) combined with reliable client-side body content search.

## Quick Start

```bash
uvx --from git+https://github.com/frederikb96/mailprobe.git mailprobe
```

### Claude Code

Add to your MCP config:

```json
{
  "mailprobe": {
    "type": "stdio",
    "command": "uvx",
    "args": ["--from", "git+https://github.com/frederikb96/mailprobe.git", "mailprobe"],
    "env": {
      "IMAP_HOST": "your-imap-server.com",
      "IMAP_USER": "your@email.com",
      "IMAP_PASSWORD": "your-password"
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `search` | Hybrid email search with body content + metadata filtering |
| `get_email` | Fetch full email content by UID |
| `download_attachment` | Download email attachments to disk |
| `list_folders` | List all mailbox folders |
| `list_accounts` | List configured accounts (no passwords) |

## Configuration

### Single Account

```
IMAP_HOST=mail.example.com
IMAP_USER=user@example.com
IMAP_PASSWORD=secret
IMAP_PORT=993  # optional, default 993
```

### Multi-Account

```
IMAP_PERSONAL_HOST=posteo.de
IMAP_PERSONAL_USER=me@posteo.net
IMAP_PERSONAL_PASSWORD=...

IMAP_WORK_HOST=mail.company.com
IMAP_WORK_USER=user@company.com
IMAP_WORK_PASSWORD=...
```

Specify `account: "personal"` or `account: "work"` in tool calls. Omitting defaults to the first account.

## How It Works

```
search(body_contains="invoice", date_from="2025-01-01", date_to="2025-06-01")

    ┌──────────────────────────┐
    │  Server-side (fast)      │  IMAP SEARCH: date range, sender, subject
    │  → narrows to ~200 msgs  │
    └──────────┬───────────────┘
               │
    ┌──────────▼───────────────┐
    │  Client-side (reliable)  │  Download & scan body text
    │  → finds 3 matches       │
    └──────────────────────────┘
```

IMAP servers with full-text search indexing (Gmail, Outlook) handle body search server-side. Servers without it (Posteo, many self-hosted) silently return 0 results. mailprobe's hybrid approach works with both.

## License

MIT
