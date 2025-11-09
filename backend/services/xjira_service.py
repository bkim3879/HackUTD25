"""Lightweight Jira client helpers used across the backend."""
from __future__ import annotations

import os
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise RuntimeError("Missing Jira credentials in backend/.env")

DEFAULT_JQL = os.getenv("JIRA_DEFAULT_JQL", 'project = "DWOS" ORDER BY priority DESC')


def _extract_description(raw) -> Optional[str]:
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        # Atlassian Document Format
        content = raw.get("content") or []
        fragments: List[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            for paragraph in block.get("content", []):
                text = paragraph.get("text")
                if text:
                    fragments.append(text)
        if fragments:
            return "\n".join(fragments)
        return raw.get("text") or str(raw)
    return str(raw)


def _request(path: str, method: str = "GET", **kwargs):
    url = f"{JIRA_BASE_URL}{path}"
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    response = requests.request(method, url, auth=auth, **kwargs)
    response.raise_for_status()
    return response


def search_issues(jql: str | None = None, max_results: int = 50) -> List[Dict[str, any]]:
    """Run a Jira search and normalize the fields our services expect."""
    payload = {
        "jql": jql or DEFAULT_JQL,
        "maxResults": max_results,
        "fields": [
            "summary",
            "description",
            "priority",
            "status",
            "assignee",
            "updated",
        ],
    }
    response = _request("/rest/api/3/search/jql", method="POST", json=payload, headers={"Accept": "application/json"})
    data = response.json()
    issues = data.get("issues", [])
    return [
        {
            "id": issue.get("id"),
            "key": issue.get("key"),
            "summary": issue.get("fields", {}).get("summary"),
            "description": _extract_description(issue.get("fields", {}).get("description")),
            "priority": (issue.get("fields", {}).get("priority") or {}).get("name"),
            "status": (issue.get("fields", {}).get("status") or {}).get("name"),
            "assignee": ((issue.get("fields", {}).get("assignee") or {}).get("displayName")),
            "updated": issue.get("fields", {}).get("updated"),
        }
        for issue in issues
    ]
