import os
import logging
import natsort
from typing import Dict, List


def comic_filter(
    source_path: str,
    comic_names: List[str],
    min_chapters: int,
    min_pages: int,
    min_pages_ratio: float,
    max_pages: int,
    logger: logging.Logger,
):
    filted_comics: Dict[str, List[str]] = {}
    for comic in comic_names:
        comic_path = os.path.join(source_path, comic)
        if not os.path.isdir(comic_path):
            continue
        chapters = []
        pages_cnt = []
        chapter_names = os.listdir(comic_path)
        for chapter in chapter_names:
            chapter_path = os.path.join(comic_path, chapter)
            if not os.path.isdir(chapter_path):
                continue
            pages = len(os.listdir(chapter_path))
            if max_pages != -1 and pages > max_pages:
                logger.info(f'Filted {chapter} in {comic}: Chapter too long')
                continue
            chapters.append(chapter)
            pages_cnt.append(pages)
        if len(chapters) < min_chapters:
            logger.info(f'Filted {comic}: Too few chapters')
            continue
        pages_cnt = sorted(pages_cnt)
        if min_pages_ratio >= 0 and pages_cnt[int(len(pages_cnt) * min_pages_ratio)] < min_pages:
            logger.info(f'Filted {comic}: Too short chapters')
            continue
        filted_comics[comic] = natsort.os_sorted(chapters)
    return filted_comics
