"""Tests for the hybrid search scan bound and ordering."""

from typing import Any
from unittest.mock import patch

from mailprobe import client
from mailprobe.config import ImapAccount


class FakeMessage:
    """Minimal stand-in for an imap_tools MailMessage."""

    def __init__(self, uid: str, text: str = "") -> None:
        self.uid = uid
        self.subject = f"subject {uid}"
        self.from_ = "sender@example.com"
        self.to: tuple[str, ...] = ("me@example.com",)
        self.cc: tuple[str, ...] = ()
        self.date = None
        self.text = text
        self.html = ""
        self.attachments: list[Any] = []


class FakeFolderManager:
    """Stand-in for MailBox.folder."""

    def __init__(self, names: list[str]) -> None:
        self._names = names
        self.current = names[0] if names else ""

    def list(self) -> list[Any]:
        return [type("Folder", (), {"name": n, "flags": []}) for n in self._names]

    def set(self, name: str) -> None:
        self.current = name


class FakeMailBox:
    """Context-manager stand-in for an imap_tools MailBox."""

    def __init__(self, messages: dict[str, list[FakeMessage]]) -> None:
        self._messages = messages
        self.folder = FakeFolderManager(list(messages))
        self.fetch_calls: list[dict[str, Any]] = []

    def login(self, user: str, password: str) -> "FakeMailBox":
        return self

    def __enter__(self) -> "FakeMailBox":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def fetch(self, criteria: Any, **kwargs: Any) -> Any:
        self.fetch_calls.append(kwargs)
        msgs = list(self._messages[self.folder.current])
        if kwargs.get("reverse"):
            msgs.reverse()
        return iter(msgs)


ACCOUNT = ImapAccount(name="test", host="mail.example.com", user="me@example.com", password="x")


def _patched(box: FakeMailBox) -> Any:
    return patch.object(client, "_connect", return_value=box)


def test_body_search_stops_at_max_scan() -> None:
    """An unmatched body search stops after max_scan messages and flags truncation."""
    box = FakeMailBox({"INBOX": [FakeMessage(str(i)) for i in range(10)]})
    with _patched(box):
        result = client.search_emails(ACCOUNT, body_contains="needle", max_scan=5)
    assert result.total_scanned == 5
    assert result.scan_truncated is True
    assert result.emails == []


def test_body_search_not_truncated_under_cap() -> None:
    """A body search that scans the whole mailbox under the cap is not flagged."""
    box = FakeMailBox({"INBOX": [FakeMessage(str(i)) for i in range(3)]})
    with _patched(box):
        result = client.search_emails(ACCOUNT, body_contains="needle", max_scan=100)
    assert result.total_scanned == 3
    assert result.scan_truncated is False


def test_body_search_fetches_newest_first_in_batches() -> None:
    """Body matching fetches newest-first and in batches, finding the recent hit."""
    box = FakeMailBox({"INBOX": [FakeMessage("1"), FakeMessage("2", text="has needle here")]})
    with _patched(box):
        result = client.search_emails(ACCOUNT, body_contains="needle", limit=1)
    assert [e.uid for e in result.emails] == ["2"]
    assert box.fetch_calls[0]["reverse"] is True
    assert box.fetch_calls[0]["bulk"] == 50
