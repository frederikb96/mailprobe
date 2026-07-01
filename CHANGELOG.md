# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-07-01

### Changed

- Body content search now fetches messages newest-first in batches and stops
  after `max_scan` messages (default 2000), returning `scan_truncated` in the
  result. Previously an unnarrowed body search downloaded every message in
  every folder one at a time, which could run for many minutes on large
  mailboxes. Narrow with `date_from`/`date_to` or `folders` to cover older mail.

## [0.1.0] - 2026-02-28

### Added

- Hybrid email search: server-side IMAP filtering + client-side body text search
- Multi-account support via environment variable groups
- Tools: search, get_email, download_attachment, list_folders, list_accounts
- Works with IMAP servers lacking full-text search indexing (e.g., Posteo)
