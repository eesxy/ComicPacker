import os
import re
import json
import toml
import natsort
from abc import ABC, abstractmethod
from .const import IMAGE_EXT
from .comic import Page, Chapter, Comic
import logging


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
        comic = Comic(comic_title, [], cover_path=cover_path)
        chapter_index = 1
        for chapter_title in natsort.os_sorted(os.listdir(path)):
            chapter_path = os.path.join(path, chapter_title)
            if not os.path.isdir(chapter_path): continue
            chapter = Chapter(chapter_index, chapter_title, [])
            page_index = 1
            for page_file in natsort.os_sorted(os.listdir(chapter_path)):
                page_path = os.path.join(chapter_path, page_file)
                page_title, ext = os.path.splitext(page_file)
                if ext not in IMAGE_EXT: continue
                page = Page(page_index, page_title, page_path)
                chapter.pages.append(page)
                page_index += 1
            comic.chapters.append(chapter)
            chapter_index += 1
        return comic


class TachiyomiParser(BaseParser):
    @classmethod
    def parse(cls, path):
        cover_path = None
        for ext in IMAGE_EXT:
            if os.path.exists(os.path.join(path, 'cover' + ext)):
                cover_path = os.path.join(path, 'cover' + ext)
                break
        comic_title = ''
        authors = None
        subjects = None
        description = None
        for file in os.listdir(path):
            if os.path.splitext(file)[1] != '.json': continue
            with open(os.path.join(path, file), 'r') as f:
                js = f.read()
                meta = json.loads(js)
                if 'title' in meta: comic_title = meta['title']
                if 'author' in meta: authors = re.split(r',|;', meta['author'])
                if 'description' in meta: description = meta['description']
                if 'genre' in meta: subjects = set(meta['genre'])
        comic = Comic(
            comic_title,
            [],
            authors=authors,
            subjects=subjects,
            description=description,
            cover_path=cover_path,
        )
        chapter_index = 1
        for chapter_title in natsort.os_sorted(os.listdir(path)):
            chapter_path = os.path.join(path, chapter_title)
            if not os.path.isdir(chapter_path): continue
            chapter = Chapter(chapter_index, chapter_title, [])
            page_index = 1
            for page_file in natsort.os_sorted(os.listdir(chapter_path)):
                page_path = os.path.join(chapter_path, page_file)
                page_title, ext = os.path.splitext(page_file)
                if ext not in IMAGE_EXT: continue
                page = Page(page_index, page_title, page_path)
                chapter.pages.append(page)
                page_index += 1
            comic.chapters.append(chapter)
            chapter_index += 1
        return comic


class DmzjBackupParser(BaseParser):
    @classmethod
    def parse(cls, path):
        cover_path = None
        for ext in IMAGE_EXT:
            if os.path.exists(os.path.join(path, 'cover' + ext)):
                cover_path = os.path.join(path, 'cover' + ext)
                break
        with open(os.path.join(path, 'details.json'), 'r') as f:
            js = f.read()
            meta = json.loads(js)
            comic_title = meta['title']
            authors = re.split(r',|;', re.sub(r'\s', '', meta['author']))
            description = meta['description']
            subjects = set(meta['genre'])
        meta = toml.load(os.path.join(path, 'info.toml'))
        chapter_list = meta['chapter_list']
        comic = Comic(
            comic_title,
            [],
            authors=authors,
            subjects=subjects,
            description=description,
            cover_path=cover_path,
        )
        chapter_index = 1
        for chapter_title in chapter_list:
            chapter_path = os.path.join(path, chapter_title)
            if not os.path.isdir(chapter_path):
                logging.getLogger('main.Parser').warning(
                    f'missing chapter {chapter_title} in {comic_title}')
                continue
            chapter = Chapter(chapter_index, chapter_title, [])
            page_index = 1
            for page_file in natsort.os_sorted(os.listdir(chapter_path)):
                page_path = os.path.join(chapter_path, page_file)
                page_title, ext = os.path.splitext(page_file)
                if ext not in IMAGE_EXT: continue
                page = Page(page_index, page_title, page_path)
                chapter.pages.append(page)
                page_index += 1
            comic.chapters.append(chapter)
            chapter_index += 1
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
        comic = Comic(comic_meta['title'], [], cover_path=cover_path)
        for chapter_id in os.listdir(path):
            chapter_path = os.path.join(path, chapter_id)
            if not os.path.isdir(chapter_path): continue
            chapter_meta = toml.load(os.path.join(chapter_path, 'meta.toml'))
            chapter = Chapter(chapter_meta['ord'], chapter_meta['title'], [])
            for index, page_file in enumerate(chapter_meta['paths']):
                page_file = os.path.split(page_file)[1]
                page_path = os.path.join(chapter_path, page_file)
                _, ext = os.path.splitext(page_file)
                page = Page(index, '{:04d}'.format(index), page_path)
                chapter.pages.append(page)
            comic.chapters.append(chapter)
        comic.chapters.sort(key=lambda x: x.order)
        return comic
