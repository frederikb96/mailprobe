"""Tests for account configuration."""

import os
from unittest.mock import patch

import pytest

from mailprobe.config import ImapAccount, discover_accounts, get_account


class TestDiscoverAccounts:
    """Tests for discover_accounts."""

    def test_single_account(self) -> None:
        """Discover a single default account from env vars."""
        env = {
            "IMAP_HOST": "mail.example.com",
            "IMAP_USER": "user@example.com",
            "IMAP_PASSWORD": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            accounts = discover_accounts()
        assert len(accounts) == 1
        assert "default" in accounts
        assert accounts["default"].host == "mail.example.com"
        assert accounts["default"].user == "user@example.com"
        assert accounts["default"].port == 993

    def test_single_account_custom_port(self) -> None:
        """Respect custom port setting."""
        env = {
            "IMAP_HOST": "mail.example.com",
            "IMAP_USER": "user@example.com",
            "IMAP_PASSWORD": "secret",
            "IMAP_PORT": "143",
        }
        with patch.dict(os.environ, env, clear=True):
            accounts = discover_accounts()
        assert accounts["default"].port == 143

    def test_multi_account(self) -> None:
        """Discover multiple named accounts."""
        env = {
            "IMAP_WORK_HOST": "work.example.com",
            "IMAP_WORK_USER": "work@example.com",
            "IMAP_WORK_PASSWORD": "secret1",
            "IMAP_PERSONAL_HOST": "personal.example.com",
            "IMAP_PERSONAL_USER": "me@example.com",
            "IMAP_PERSONAL_PASSWORD": "secret2",
        }
        with patch.dict(os.environ, env, clear=True):
            accounts = discover_accounts()
        assert len(accounts) == 2
        assert "work" in accounts
        assert "personal" in accounts
        assert accounts["work"].host == "work.example.com"
        assert accounts["personal"].host == "personal.example.com"

    def test_no_accounts(self) -> None:
        """Return empty dict when no IMAP env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            accounts = discover_accounts()
        assert len(accounts) == 0

    def test_mixed_single_and_named(self) -> None:
        """Discover both default and named accounts."""
        env = {
            "IMAP_HOST": "default.example.com",
            "IMAP_USER": "default@example.com",
            "IMAP_PASSWORD": "secret0",
            "IMAP_WORK_HOST": "work.example.com",
            "IMAP_WORK_USER": "work@example.com",
            "IMAP_WORK_PASSWORD": "secret1",
        }
        with patch.dict(os.environ, env, clear=True):
            accounts = discover_accounts()
        assert len(accounts) == 2
        assert "default" in accounts
        assert "work" in accounts


class TestGetAccount:
    """Tests for get_account."""

    def test_get_default(self) -> None:
        """Get first account when no name specified."""
        env = {
            "IMAP_HOST": "mail.example.com",
            "IMAP_USER": "user@example.com",
            "IMAP_PASSWORD": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            acc = get_account()
        assert acc.host == "mail.example.com"

    def test_get_named(self) -> None:
        """Get account by name."""
        env = {
            "IMAP_WORK_HOST": "work.example.com",
            "IMAP_WORK_USER": "work@example.com",
            "IMAP_WORK_PASSWORD": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            acc = get_account("work")
        assert acc.host == "work.example.com"

    def test_get_missing_raises(self) -> None:
        """Raise ValueError for unknown account name."""
        env = {
            "IMAP_HOST": "mail.example.com",
            "IMAP_USER": "user@example.com",
            "IMAP_PASSWORD": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="nonexistent"):
                get_account("nonexistent")

    def test_no_accounts_raises(self) -> None:
        """Raise ValueError when no accounts configured."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No IMAP accounts"):
                get_account()
