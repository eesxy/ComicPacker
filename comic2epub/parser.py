import os
import toml
import natsort
from abc import ABC, abstractmethod
from .const import IMAGE_EXT
from .comic import Page, Chapter, Comic


class BaseParser:
    @classmethod
    @abstractmethod
    def parse(cls, path: str) -> Comic:
        raise NotImplementedError


class GeneralParser(BaseParser):
    @classmethod
    def parse(cls, path):
        comic_title = os.path.basename(path)
        cover_path = None
        for ext in IMAGE_EXT:
            if os.path.exists(os.path.join(path, 'cover' + ext)):
                cover_path = os.path.join(path, 'cover' + ext)
                break
        comic = Comic(comic_title, cover_path, [])
        index = 1
        for chapter_title in natsort.os_sorted(os.listdir(path)):
            chapter_path = os.path.join(path, chapter_title)
            if not os.path.isdir(chapter_path): continue
            chapter = Chapter(index, chapter_title, [])
            for page_file in natsort.os_sorted(os.listdir(chapter_path)):
                page_path = os.path.join(chapter_path, page_file)
                page_title, ext = os.path.splitext(page_file)
                if ext not in IMAGE_EXT: continue
                page = Page(page_title, page_path)
                chapter.pages.append(page)
            comic.chapters.append(chapter)
            index += 1
        return comic


class BcdownParser(BaseParser):
    @classmethod
    def parse(cls, path):
        comic_meta = toml.load(os.path.join(path, 'meta.toml'))
        cover_path = None
        for ext in IMAGE_EXT:
            if os.path.exists(os.path.join(path, 'cover' + ext)):
                cover_path = os.path.join(path, 'cover' + ext)
                break
        comic = Comic(comic_meta['title'], cover_path, [])
        for chapter_id in os.listdir(path):
            chapter_path = os.path.join(path, chapter_id)
            if not os.path.isdir(chapter_path): continue
            chapter_meta = toml.load(os.path.join(chapter_path, 'meta.toml'))
            chapter = Chapter(chapter_meta['ord'], chapter_meta['title'], [])
            for index, page_file in enumerate(chapter_meta['paths']):
                page_file = os.path.split(page_file)[1]
                page_path = os.path.join(chapter_path, page_file)
                _, ext = os.path.splitext(page_file)
                if ext not in IMAGE_EXT: continue
                page = Page('{:04d}'.format(index), page_path)
                chapter.pages.append(page)
            comic.chapters.append(chapter)
        comic.chapters.sort(key=lambda x: x.order)
        return comic