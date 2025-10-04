from typing import Any

import httpx
from app.schema import Commit, FileChange

BASE_URL = "https://api.github.com/repos"


class GithubClient:
    def __init__(self, owner: str, repo: str, branch: str, token: str | None = None):
        self.owner = owner
        self.repo = repo
        self.branch = branch

        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._client = httpx.AsyncClient(headers=headers, timeout=10.0)

    async def get_commit_log(self, limit: int = 10) -> list[Commit]:
        url = f"{BASE_URL}/{self.owner}/{self.repo}/commits"
        params: dict[str, str] = {"sha": self.branch, "per_page": str(limit)}
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        commits_data = response.json()

        return [
            Commit(
                sha=commit_data["sha"],
                author_name=commit_data["commit"]["author"]["name"],
                author_email=commit_data["commit"]["author"]["email"],
                date=commit_data["commit"]["author"]["date"],
                message=commit_data["commit"]["message"],
                html_url=commit_data["html_url"],
            )
            for commit_data in commits_data
        ]

    async def get_commit_changes(self, sha: str) -> list[FileChange]:
        url = f"{BASE_URL}/{self.owner}/{self.repo}/commits/{sha}"
        response = await self._client.get(url)
        response.raise_for_status()
        commit_data = response.json()

        return [
            FileChange(
                path=file_data["filename"],
                status=file_data["status"],
                additions=file_data["additions"],
                deletions=file_data["deletions"],
                previous_filename=file_data.get("previous_filename"),
                patch=file_data.get("patch"),
            )
            for file_data in commit_data.get("files", [])
        ]

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        await self._client.aclose()
