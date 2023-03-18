from dataclasses import dataclass
from typing import List, Optional


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
    cover_path: Optional[str]
    chapters: List[Chapter]
