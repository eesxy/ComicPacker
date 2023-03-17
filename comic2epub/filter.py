import logging
from .comic import Comic


class ComicFilter:
    def __init__(
        self,
        min_chapters: int,
        min_pages: int,
        min_pages_ratio: float,
        logger: logging.Logger,
    ) -> None:
        self.min_chapters = min_chapters
        self.min_pages = min_pages
        self.min_pages_ratio = min_pages_ratio
        self.logger = logger.getChild('Filter')

    def filt(self, comic: Comic) -> bool:
        if self.min_chapters != -1 and len(comic.chapters) < self.min_chapters:
            self.logger.info(f'Too few chapters: {comic.title}')
            return False
        pages_cnt = []
        for chapter in comic.chapters:
            page_num = len(chapter.pages)
            pages_cnt.append(page_num)
        pages_cnt.sort()
        if self.min_pages_ratio >= 0 and pages_cnt[int(
                len(pages_cnt) * self.min_pages_ratio)] < self.min_pages:
            self.logger.info(f'Too many short chapters: {comic.title}')
            return False
        return True


class ChapterFilter:
    def __init__(
        self,
        max_pages: int,
        logger: logging.Logger,
    ) -> None:
        self.max_pages = max_pages
        self.logger = logger.getChild('Filter')

    def filt(self, comic: Comic) -> None:
        filted_chapters = []
        for chapter in comic.chapters:
            page_num = len(chapter.pages)
            if self.max_pages != -1 and page_num > self.max_pages:
                self.logger.info(f'Chapter too long: {chapter.title} in {comic.title}')
            else:
                filted_chapters.append(chapter)
        comic.chapters = filted_chapters
        return
