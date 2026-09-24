#!/usr/bin/env python3
"""
Update the "RECENTLY UPDATED" section of a GitHub profile README.

Environment variables:
  GH_OWNER  - GitHub username / organization owner
  GH_TOKEN  - Optional GitHub token for API requests

The script uses GitHub's public REST API and updates only the section
between these README markers:

<!-- PROJECTS:START -->
<!-- PROJECTS:END -->
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


README_PATH = Path("README.md")
START_MARKER = "<!-- PROJECTS:START -->"
END_MARKER = "<!-- PROJECTS:END -->"
MAX_REPOS = 6


def github_get(url: str, token: str | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-profile-readme-updater",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(
            f"GitHub API returned HTTP {exc.code} for {url}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach GitHub API: {exc.reason}") from exc


def clean_text(value: str | None) -> str:
    """Keep generated Markdown tables from breaking on multiline descriptions."""
    if not value:
        return "No description"
    return " ".join(value.replace("|", r"\|").split())


def format_date(value: str) -> str:
    """Convert GitHub's ISO timestamp into a compact date."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return value[:10]


def build_projects_table(repositories: list[dict], owner: str) -> str:
    rows: list[str] = []

    for repo in repositories:
        # Skip the special profile repository itself.
        if repo.get("name", "").lower() == owner.lower():
            continue

        # Skip forks so the section represents projects the account owns.
        if repo.get("fork", False):
            continue

        name = repo.get("name", "Unnamed")
        url = repo.get("html_url", "#")
        description = clean_text(repo.get("description"))
        language = repo.get("language") or "—"
        updated = format_date(repo.get("updated_at", ""))

        rows.append(
            f"| [{name}]({url}) | {description} | "
            f"{language} | {updated} |"
        )

        if len(rows) >= MAX_REPOS:
            break

    if not rows:
        rows.append(
            "| _No public repositories found yet._ | — | — | — |"
        )

    return (
        "| Repository | Description | Language | Updated |\n"
        "|---|---|---|---|\n"
        + "\n".join(rows)
    )


def update_readme(table: str) -> None:
    if not README_PATH.exists():
        raise FileNotFoundError(f"{README_PATH} was not found.")

    text = README_PATH.read_text(encoding="utf-8")

    if START_MARKER not in text or END_MARKER not in text:
        raise ValueError(
            "README markers were not found. Expected "
            f"{START_MARKER} and {END_MARKER}."
        )

    start = text.index(START_MARKER) + len(START_MARKER)
    end = text.index(END_MARKER)

    replacement = f"\n{table}\n"
    updated_text = text[:start] + replacement + text[end:]

    README_PATH.write_text(updated_text, encoding="utf-8")


def main() -> int:
    owner = os.getenv("GH_OWNER") or os.getenv("GITHUB_REPOSITORY_OWNER")

    if not owner:
        print(
            "Missing GH_OWNER or GITHUB_REPOSITORY_OWNER.",
            file=sys.stderr,
        )
        return 1

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")

    api_url = (
        f"https://api.github.com/users/{owner}/repos"
        "?per_page=100&sort=updated&direction=desc"
    )

    try:
        repositories = github_get(api_url, token=token)

        if not isinstance(repositories, list):
            raise RuntimeError("Unexpected GitHub API response.")

        table = build_projects_table(repositories, owner)
        update_readme(table)

        print(
            f"Updated README.md with up to {MAX_REPOS} "
            f"recently updated repositories for @{owner}."
        )
        return 0

    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
