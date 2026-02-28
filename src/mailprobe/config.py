"""IMAP account configuration from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ImapAccount:
    """IMAP account connection details."""

    name: str
    host: str
    user: str
    password: str
    port: int = 993


def discover_accounts() -> dict[str, ImapAccount]:
    """Discover IMAP accounts from environment variables.

    Supports two patterns:
    - Single account: IMAP_HOST, IMAP_USER, IMAP_PASSWORD, IMAP_PORT
    - Multi-account: IMAP_<NAME>_HOST, IMAP_<NAME>_USER, IMAP_<NAME>_PASSWORD, IMAP_<NAME>_PORT

    Returns:
        Dictionary mapping account names to ImapAccount instances.
    """
    accounts: dict[str, ImapAccount] = {}

    if os.environ.get("IMAP_HOST"):
        accounts["default"] = ImapAccount(
            name="default",
            host=os.environ["IMAP_HOST"],
            user=os.environ["IMAP_USER"],
            password=os.environ["IMAP_PASSWORD"],
            port=int(os.environ.get("IMAP_PORT", "993")),
        )

    seen_prefixes: set[str] = set()
    for key in os.environ:
        if key.startswith("IMAP_") and key.endswith("_HOST") and key != "IMAP_HOST":
            prefix = key[5:-5]
            if prefix and prefix not in seen_prefixes:
                seen_prefixes.add(prefix)
                name = prefix.lower()
                accounts[name] = ImapAccount(
                    name=name,
                    host=os.environ[f"IMAP_{prefix}_HOST"],
                    user=os.environ[f"IMAP_{prefix}_USER"],
                    password=os.environ[f"IMAP_{prefix}_PASSWORD"],
                    port=int(os.environ.get(f"IMAP_{prefix}_PORT", "993")),
                )

    return accounts


def get_account(name: str | None = None) -> ImapAccount:
    """Get an IMAP account by name.

    Args:
        name: Account name. None returns the first/only account.

    Returns:
        The requested ImapAccount.

    Raises:
        ValueError: If no accounts configured or name not found.
    """
    accounts = discover_accounts()
    if not accounts:
        msg = "No IMAP accounts configured. Set IMAP_HOST, IMAP_USER, IMAP_PASSWORD environment variables."
        raise ValueError(msg)

    if name is None:
        return next(iter(accounts.values()))

    if name not in accounts:
        available = ", ".join(accounts.keys())
        raise ValueError(f"Account '{name}' not found. Available: {available}")

    return accounts[name]
