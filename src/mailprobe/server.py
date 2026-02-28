"""MCP server with IMAP email tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from mailprobe import client
from mailprobe.config import discover_accounts, get_account

mcp = FastMCP(
    "mailprobe",
    instructions="IMAP email search with hybrid full-text body search for servers without FTS indexing",
)


@mcp.tool()
def search(
    body_contains: str | None = None,
    subject_contains: str | None = None,
    from_contains: str | None = None,
    to_contains: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    folders: list[str] | None = None,
    limit: int = 50,
    account: str | None = None,
) -> dict[str, Any]:
    """Search emails with hybrid full-text body search.

    Uses server-side IMAP filtering for metadata (date, subject, from, to) and
    client-side filtering for body content. Works reliably on servers without
    full-text search indexing (e.g., Posteo).

    Args:
        body_contains: Text to find in email body (client-side, case-insensitive).
        subject_contains: Filter by subject (server-side IMAP).
        from_contains: Filter by sender (server-side).
        to_contains: Filter by recipient (server-side).
        date_from: Start date inclusive (ISO: YYYY-MM-DD).
        date_to: End date exclusive (ISO: YYYY-MM-DD).
        folders: Specific folders to search. Default: all folders.
        limit: Maximum results (default: 50).
        account: Account name for multi-account setups.
    """
    acc = get_account(account)
    result = client.search_emails(
        acc,
        body_contains=body_contains,
        subject_contains=subject_contains,
        from_contains=from_contains,
        to_contains=to_contains,
        date_from=date_from,
        date_to=date_to,
        folders=folders,
        limit=limit,
    )
    return {
        "emails": [_summary_to_dict(e) for e in result.emails],
        "total_scanned": result.total_scanned,
        "folders_searched": result.folders_searched,
        "search_time_seconds": result.search_time_seconds,
    }


@mcp.tool()
def get_email(
    folder: str,
    uid: str,
    account: str | None = None,
) -> dict[str, Any]:
    """Get full email content by UID.

    Args:
        folder: Mailbox folder containing the email.
        uid: Email UID from search results.
        account: Account name for multi-account setups.
    """
    acc = get_account(account)
    email = client.get_email(acc, folder, uid)
    return {
        "uid": email.uid,
        "subject": email.subject,
        "from": email.from_,
        "to": email.to,
        "cc": email.cc,
        "date": email.date,
        "folder": email.folder,
        "text": email.text,
        "html": email.html,
        "attachments": email.attachments,
    }


@mcp.tool()
def download_attachment(
    folder: str,
    uid: str,
    filename: str,
    save_path: str | None = None,
    account: str | None = None,
) -> dict[str, str]:
    """Download an email attachment to disk.

    Args:
        folder: Mailbox folder containing the email.
        uid: Email UID from search results.
        filename: Attachment filename to download.
        save_path: Local path to save. Default: /tmp/mailprobe/attachments/<filename>.
        account: Account name for multi-account setups.
    """
    acc = get_account(account)
    path = client.download_attachment(acc, folder, uid, filename, save_path)
    return {"saved_to": str(path), "filename": filename}


@mcp.tool()
def list_folders(account: str | None = None) -> dict[str, Any]:
    """List all mailbox folders.

    Args:
        account: Account name for multi-account setups.
    """
    acc = get_account(account)
    folders = client.list_folders(acc)
    return {"folders": folders}


@mcp.tool()
def list_accounts() -> dict[str, Any]:
    """List configured IMAP accounts (without passwords)."""
    accounts = discover_accounts()
    return {
        "accounts": [{"name": a.name, "host": a.host, "user": a.user} for a in accounts.values()],
    }


def _summary_to_dict(email: client.EmailSummary) -> dict[str, Any]:
    """Convert EmailSummary to serializable dict."""
    return {
        "uid": email.uid,
        "subject": email.subject,
        "from": email.from_,
        "to": email.to,
        "date": email.date,
        "folder": email.folder,
        "has_attachments": email.has_attachments,
        "attachment_names": email.attachment_names,
    }
