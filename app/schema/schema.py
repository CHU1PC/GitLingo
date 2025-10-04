from argparse import Namespace

from pydantic import BaseModel


class Args(Namespace):
    owner: str
    repo: str


class Commit(BaseModel):
    sha: str
    author_name: str
    author_email: str
    date: str
    message: str
    html_url: str


class FileChange(BaseModel):
    path: str
    status: str
    additions: int
    deletions: int
    previous_filename: str | None
    patch: str | None
