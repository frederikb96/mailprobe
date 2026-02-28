# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-02-28

### Added

- Hybrid email search: server-side IMAP filtering + client-side body text search
- Multi-account support via environment variable groups
- Tools: search, get_email, download_attachment, list_folders, list_accounts
- Works with IMAP servers lacking full-text search indexing (e.g., Posteo)
