import os
import zipfile
import itertools
from typing import Optional
from dataclasses import dataclass
from jinja2 import Environment


@dataclass(eq=False)
class ComicInfoPage:
    image: int
    bookmark: str


def safestr(s: str):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(
        '\"', '&quot;').replace('\'', '&apos;')


class ComicCbz:
    def __init__(
        self,
        filename,
        title: str,
        writer: Optional[str] = None,
        publisher: Optional[str] = None,
        genre: Optional[str] = None,
        summary: Optional[str] = None,
        language: Optional[str] = "zh",
    ):
        if '.cbz' not in filename:
            filename += '.cbz'

        full_file_name = os.path.expanduser(filename)
        path = os.path.split(full_file_name)[0]
        if not os.path.exists(path):
            os.makedirs(path)
        self.cbz = zipfile.ZipFile(full_file_name, 'w', allowZip64=True)
        self.index = itertools.count()
        self.pages = None

        self.title = safestr(title)
        self.writer = safestr(writer) if writer is not None else None
        self.publisher = safestr(publisher) if publisher is not None else None
        self.genre = safestr(genre) if genre is not None else None
        self.summary = safestr(summary) if summary is not None else None
        self.language = language

    def add_comic_page(self, image_data, image_ext, chapter: Optional[str] = None,
                       page: Optional[str] = None, nav_label: Optional[str] = None):
        index = next(self.index)
        if chapter is None: chapter = ''
        else: chapter = chapter + '/'
        if page is None: page = str(index)
        page_name = chapter + page + image_ext
        self.cbz.writestr(page_name, image_data)
        if nav_label is not None:
            if self.pages is None: self.pages = []
            self.pages.append(ComicInfoPage(index, safestr(nav_label)))

    def save(self):
        with open(os.path.join(os.path.dirname(__file__), './ComicInfo.xml'), 'r',
                  encoding='utf-8') as f:
            template = f.read()
        comicinfo = Environment().from_string(template).render(
            title=self.title,
            writer=self.writer,
            publisher=self.publisher,
            genre=self.genre,
            summary=self.summary,
            language=self.language,
            pages=self.pages,
        )
        self.cbz.writestr('ComicInfo.xml', comicinfo)
        self.cbz.close()
