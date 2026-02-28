"""IMAP operations with hybrid full-text body search."""

import datetime
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from imap_tools import AND, MailBox

from mailprobe.config import ImapAccount


@dataclass
class EmailSummary:
    """Summary of an email message."""

    uid: str
    subject: str
    from_: str
    to: list[str]
    date: str
    folder: str
    has_attachments: bool
    attachment_names: list[str] = field(default_factory=list)


@dataclass
class EmailDetail:
    """Full email content."""

    uid: str
    subject: str
    from_: str
    to: list[str]
    cc: list[str]
    date: str
    folder: str
    text: str
    html: str
    attachments: list[dict[str, str | int]] = field(default_factory=list)


@dataclass
class SearchResult:
    """Search operation results."""

    emails: list[EmailSummary]
    total_scanned: int
    folders_searched: list[str]
    search_time_seconds: float


def _connect(account: ImapAccount) -> MailBox:
    """Create an IMAP connection."""
    return MailBox(account.host, account.port)


def list_folders(account: ImapAccount) -> list[dict[str, Any]]:
    """List all mailbox folders.

    Args:
        account: IMAP account to use.

    Returns:
        List of folder info dicts with name and flags.
    """
    with _connect(account).login(account.user, account.password) as mb:
        return [{"name": f.name, "flags": list(f.flags)} for f in mb.folder.list()]


def search_emails(
    account: ImapAccount,
    *,
    body_contains: str | None = None,
    subject_contains: str | None = None,
    from_contains: str | None = None,
    to_contains: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    folders: list[str] | None = None,
    limit: int = 50,
) -> SearchResult:
    """Search emails with hybrid server+client-side filtering.

    Server-side IMAP SEARCH handles metadata filters (date, subject, from, to).
    Client-side filtering handles body content for servers without FTS indexing.

    Args:
        account: IMAP account to use.
        body_contains: Text to find in email body (client-side, case-insensitive).
        subject_contains: Filter by subject (server-side).
        from_contains: Filter by sender (server-side).
        to_contains: Filter by recipient (server-side).
        date_from: Start date inclusive, ISO format YYYY-MM-DD.
        date_to: End date exclusive, ISO format YYYY-MM-DD.
        folders: Specific folders to search. None searches all.
        limit: Maximum results to return.

    Returns:
        SearchResult with matching emails and search metadata.
    """
    start = time.time()
    results: list[EmailSummary] = []
    total_scanned = 0
    searched_folders: list[str] = []

    with _connect(account).login(account.user, account.password) as mb:
        folder_list = folders if folders is not None else [f.name for f in mb.folder.list()]

        for folder_name in folder_list:
            try:
                mb.folder.set(folder_name)
            except Exception:
                continue

            searched_folders.append(folder_name)
            criteria = _build_criteria(
                subject_contains=subject_contains,
                from_contains=from_contains,
                to_contains=to_contains,
                date_from=date_from,
                date_to=date_to,
            )

            for msg in mb.fetch(criteria, mark_seen=False):
                total_scanned += 1

                if body_contains:
                    body_text = (msg.text or "") + (msg.html or "")
                    if body_contains.lower() not in body_text.lower():
                        continue

                results.append(
                    EmailSummary(
                        uid=msg.uid or "",
                        subject=msg.subject,
                        from_=msg.from_,
                        to=list(msg.to),
                        date=msg.date.isoformat() if msg.date else "",
                        folder=folder_name,
                        has_attachments=bool(msg.attachments),
                        attachment_names=[a.filename for a in msg.attachments],
                    )
                )

                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break

    return SearchResult(
        emails=results,
        total_scanned=total_scanned,
        folders_searched=searched_folders,
        search_time_seconds=round(time.time() - start, 2),
    )


def get_email(account: ImapAccount, folder: str, uid: str) -> EmailDetail:
    """Fetch full email content by UID.

    Args:
        account: IMAP account to use.
        folder: Mailbox folder containing the email.
        uid: Email UID.

    Returns:
        Full email detail.

    Raises:
        ValueError: If email not found.
    """
    with _connect(account).login(account.user, account.password) as mb:
        mb.folder.set(folder)
        for msg in mb.fetch(AND(uid=uid), mark_seen=False):
            return EmailDetail(
                uid=msg.uid or "",
                subject=msg.subject,
                from_=msg.from_,
                to=list(msg.to),
                cc=list(msg.cc),
                date=msg.date.isoformat() if msg.date else "",
                folder=folder,
                text=msg.text or "",
                html=msg.html or "",
                attachments=[
                    {"filename": a.filename, "content_type": a.content_type, "size": len(a.payload)}
                    for a in msg.attachments
                ],
            )
    raise ValueError(f"Email UID {uid} not found in folder '{folder}'")


def download_attachment(
    account: ImapAccount,
    folder: str,
    uid: str,
    filename: str,
    save_path: str | None = None,
) -> Path:
    """Download an email attachment.

    Args:
        account: IMAP account to use.
        folder: Mailbox folder containing the email.
        uid: Email UID.
        filename: Attachment filename to download.
        save_path: Where to save. Defaults to /tmp/mailprobe/attachments/<filename>.

    Returns:
        Path to saved file.

    Raises:
        ValueError: If email or attachment not found.
    """
    target = Path(save_path) if save_path else Path("/tmp/mailprobe/attachments") / filename

    with _connect(account).login(account.user, account.password) as mb:
        mb.folder.set(folder)
        for msg in mb.fetch(AND(uid=uid), mark_seen=False):
            for att in msg.attachments:
                if att.filename == filename:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(att.payload)
                    return target
            available = [a.filename for a in msg.attachments]
            raise ValueError(f"Attachment '{filename}' not found. Available: {available}")
    raise ValueError(f"Email UID {uid} not found in folder '{folder}'")


def _build_criteria(
    *,
    subject_contains: str | None = None,
    from_contains: str | None = None,
    to_contains: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> Any:
    """Build IMAP SEARCH criteria from filters.

    Args:
        subject_contains: Filter by subject text.
        from_contains: Filter by sender.
        to_contains: Filter by recipient.
        date_from: Start date inclusive (ISO format).
        date_to: End date exclusive (ISO format).

    Returns:
        IMAP search criteria (AND object or 'ALL' string).
    """
    kwargs: dict[str, Any] = {}

    if date_from:
        kwargs["date_gte"] = datetime.date.fromisoformat(date_from)
    if date_to:
        kwargs["date_lt"] = datetime.date.fromisoformat(date_to)
    if subject_contains:
        kwargs["subject"] = subject_contains
    if from_contains:
        kwargs["from_"] = from_contains
    if to_contains:
        kwargs["to"] = to_contains

    if not kwargs:
        return "ALL"
    return AND(**kwargs)
