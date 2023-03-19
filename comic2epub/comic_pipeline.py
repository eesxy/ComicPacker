import logging
from abc import abstractmethod
from tqdm import tqdm
from typing import Dict
from imagededup.methods import PHash, DHash, WHash, AHash
from .comic import Comic, Chapter, Page


class BaseFilter:
    @abstractmethod
    def __call__(self, comic: Comic) -> bool:
        raise NotImplementedError


class ComicFilter(BaseFilter):
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

    def __call__(self, comic):
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


class ChapterFilter(BaseFilter):
    def __init__(
        self,
        max_pages: int,
        logger: logging.Logger,
    ) -> None:
        self.max_pages = max_pages
        self.logger = logger.getChild('Filter')

    def __call__(self, comic):
        filted_chapters = []
        for chapter in comic.chapters:
            page_num = len(chapter.pages)
            if self.max_pages != -1 and page_num > self.max_pages:
                self.logger.info(f'Chapter too long: {chapter.title} in {comic.title}')
            else:
                filted_chapters.append(chapter)
        comic.chapters = filted_chapters
        return True


class ImageDedup(BaseFilter):
    def __init__(self, method: str, logger: logging.Logger) -> None:
        if method == 'phash':
            self.image_hash = PHash(verbose=False)
        elif method == 'dhash':
            self.image_hash = DHash(verbose=False)
        elif method == 'whash':
            self.image_hash = WHash(verbose=False)
        elif method == 'ahash':
            self.image_hash = AHash(verbose=False)
        else:
            raise ValueError(f'Invalid hash method {method}')
        self.logger = logger.getChild('dedup')

    def __call__(self, comic):
        hash_dict: Dict[str, int] = {}
        self.logger.info(f'Deduping {comic.title}')
        for chapter in tqdm(comic.chapters, position=0, desc='chapters'):
            for page in tqdm(chapter.pages, position=1, desc='pages   ', leave=False):
                page.hash_code = self.image_hash.encode_image(page.path)
                if page.hash_code not in hash_dict:
                    hash_dict[page.hash_code] = 1
                else:
                    hash_dict[page.hash_code] += 1
        dup_hashes = set()
        copyright_chapter = Chapter(float('inf'), 'copyright', [])
        # All duplicate pages are considered copyright pages
        for chapter in comic.chapters:
            page_list = []
            for page in chapter.pages:
                if hash_dict[page.hash_code] > 1:  # type: ignore
                    if page.hash_code not in dup_hashes:
                        dup_hashes.add(page.hash_code)
                        new_page = Page(order=len(dup_hashes),
                                        title='{:04d}'.format(len(dup_hashes)), path=page.path)
                        copyright_chapter.pages.append(new_page)
                else:
                    page_list.append(page)
            chapter.pages = page_list
        comic.chapters.append(copyright_chapter)
        return True


class ComicPipeline:
    def __init__(self, *filters: BaseFilter) -> None:
        self.filters = list(filters)

    def append(self, filter: BaseFilter):
        self.filters.append(filter)

    def __call__(self, comic: Comic) -> bool:
        for filter in self.filters:
            if filter(comic) is False:
                return False
        return True
