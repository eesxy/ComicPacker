from copy import copy
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass(eq=False)
class Page:
    order: float
    title: str
    path: str


@dataclass(eq=False)
class Chapter:
    order: float
    title: str
    pages: List[Page]


@dataclass(eq=False)
class Comic:
    title: str
    chapters: List[Chapter]
    authors: Optional[List[str]] = None
    publisher: Optional[str] = None
    subjects: Optional[Set[str]] = None
    description: Optional[str] = None
    cover_path: Optional[str] = None

    def copy_meta(self):
        new_comic = copy(self)
        new_comic.chapters = []
        return new_comic
