import asyncio
import os
from argparse import ArgumentParser

from app.logs.get_log import GithubClient
from app.schema import Args, FileChange


def parse_args() -> Args:
    parser = ArgumentParser()
    parser.add_argument(
        "--owner",
        type=str,
        required=True,
        help="The owner of the GitHub repository",
    )
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="The name of the GitHub repository",
    )
    parser.add_argument(
        "--branch",
        type=str,
        required=False,
        default="main",
        help="The branch to fetch commits from (default: main)",
    )

    return parser.parse_args(namespace=Args())


def print_colored_patch(patch_text: str | None) -> None:
    """patchテキストを行ごとに色付けして表示する"""
    if not patch_text:
        print("  (No patch text available)")
        return

    for line in patch_text.splitlines():
        if line.startswith("+"):
            print(f"\033[92m{line}\033[0m")
        elif line.startswith("-"):
            # ANSIエスケープシーケンスで赤色にする
            print(f"\033[91m{line}\033[0m")
        else:
            print(line)


async def run_task(client: GithubClient) -> None:
    commits = await client.get_commit_log(limit=5)
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(client.get_commit_changes(commit.sha)) for commit in commits
        ]
    changes_per_commit: list[list[FileChange]] = [await task for task in tasks]

    most_recent_commit = commits[0]
    changes_for_latest = changes_per_commit[0]

    print(
        f"🧩 Latest Commit: {most_recent_commit.sha[:7]} {most_recent_commit.message}"
    )
    print(
        f"👤 Author: {most_recent_commit.author_name} <{most_recent_commit.author_email}>"
    )
    print(f"📅 Date: {most_recent_commit.date}")
    print("-" * 50)
    if not changes_for_latest:
        print("This commit has no file changes.")
        return

    for change in changes_for_latest:
        print(
            f"\n📄 File: {change.path} | Status: {change.status} "
            f"(+{change.additions} / -{change.deletions})"
        )

        print_colored_patch(change.patch)


async def main() -> None:
    args = parse_args()
    owner = args.owner
    repo = args.repo
    branch = args.branch
    token = os.environ.get("GITHUB_TOKEN")

    try:
        async with GithubClient(owner, repo, branch, token) as client:
            await run_task(client)
    except* Exception as eg:
        print(f"APIリクエスト中にエラーが発生しました。{len(eg.exceptions)}件のエラー:")
        for e in eg.exceptions:
            print(f"予期せぬエラーが発生しました: {e}")


if __name__ == "__main__":
    asyncio.run(main())
