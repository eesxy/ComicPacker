import os
import zipfile
import uuid
import datetime
from typing import Tuple, List, Set, Optional
from mimetypes import MimeTypes
from .render import render_mimetype
from .render import render_container_xml
from .render import render_navigation_documents_xhtml
from .render import render_standard_opf
from .render import render_xhtml
from .render import get_fixed_layout_jp_css


class ComicEpub:
    """
    This ComicEpub class is dedicated to generating ditigal comic EPUB files conataining image-only content.
    """
    def __init__(
        self,
        filename,
        title: Tuple[str, str],
        subjects: Optional[Set[str]] = None,
        authors: Optional[List[Tuple[str, str, str]]] = None,
        publisher: Optional[Tuple[str, str]] = None,
        epubid: str = str(uuid.uuid1()),
        language: str = "zh-CN",
        updated_date: str = datetime.datetime.now().isoformat(),
        view_width: int = 848,
        view_height: int = 1200,
        reading_order: str = 'ltr',
    ):
        """
        Create a zip file as an EPUB container, which is only epub-valid after calling the save() method.

        :rtype: instance of ComicEpub
        :param filename: epub file path to save
        :param title: epub title - Tuple(title, file_as) - Default: None
        :param authors: epub authors - List of Tuple(author_name, file_as) - Default: None
        :param publisher: epub publisher - Tuple(publisher_name, file_as) - Default: None
        :param epubid: unique epub id - Default: random uuid
        :param language: epub language - Default: zh-CN
        :param updated_date: epub updated_date - Default: current time
        :param view_width: epub view_width - Default: 848
        :param view_height: epub view_height - Default: 1200
        """
        self.title = title
        self.subjects = subjects
        self.authors = authors
        self.publisher = publisher

        self.epubid = epubid
        self.language = language
        self.updated_date = updated_date
        self.view_width = view_width
        self.view_height = view_height
        self.reading_order = reading_order

        self.manifest_images: List[Tuple[str, str, str, str]] = []
        self.manifest_xhtmls: List[Tuple[str, str]] = []
        self.manifest_spines: List[str] = []

        self.nav_title = "Navigation"
        self.nav_items: List[Tuple[str, str]] = []

        self.epub = self.__open(filename)

        self.mime = MimeTypes()

    def __open(self, filename):

        if '.epub' not in filename:
            filename += '.epub'

        full_file_name = os.path.expanduser(filename)
        path = os.path.split(full_file_name)[0]
        if not os.path.exists(path):
            os.makedirs(path)
        return zipfile.ZipFile(full_file_name, 'w', allowZip64=True)

    def __close(self):
        self.epub.close()

    def __add_image(self, index: int, image_data, image_ext, page_name: str, cover: bool = False):
        if cover:
            image_id = "cover"
        else:
            image_id = "i-" + "%05d" % index

        path = "item/image/" + page_name + image_ext
        self.epub.writestr(path, image_data)

        mimetype = self.mime.guess_type('test' + image_ext)
        if mimetype[0] is None:
            image_mimetype = "image/jpeg"
        else:
            image_mimetype = mimetype[0]
        return image_id, image_ext, image_mimetype

    def __add_xhtml(self, index: int, title: str, image_id: str, image_ext: str, page_name: str,
                    cover: bool = False):
        if cover:
            xhtml_id = "p-cover"
        else:
            xhtml_id = "p-" + "%05d" % index

        content = render_xhtml(title, image_id, image_ext, page_name, self.view_width,
                               self.view_height, cover)
        self.epub.writestr("item/xhtml/" + xhtml_id + ".xhtml", content)
        return xhtml_id

    def add_comic_page(self, image_data, image_ext, chapter: Optional[str] = None,
                       page: Optional[str] = None, cover=False, nav_label: Optional[str] = None):
        """
        Add images to the page in order, each image is a page.

        :param image_data: data of image
        :param image_ext: extension of image
        :param chapter: name of this chapter, if None, place this page in item/image/ folder
        :param page: name of this page, if None, use id as name
        :param cover: true if image is cover
        :param nav_label: if not None, create a navigation label at this page
        """
        index = len(self.manifest_xhtmls)
        if chapter is None: chapter = ''
        else: chapter = chapter + '/'
        if page is None: page = str(index)
        page_name = chapter + page
        image_id, image_ext, image_mimetype = self.__add_image(index, image_data, image_ext,
                                                               page_name, cover)
        xhtml_id = self.__add_xhtml(index, self.title[0], image_id, image_ext, page_name, cover)

        self.manifest_images.append((image_id, page_name, image_ext, image_mimetype))
        self.manifest_xhtmls.append((xhtml_id, image_id))
        # cover will not be included in spine
        if not cover:
            self.manifest_spines.append(xhtml_id)
        if nav_label is not None:
            self.nav_items.append((xhtml_id, nav_label))

    def save(self):
        """
        generate epub required files, then close and save epub file.
        """
        self.epub.writestr("mimetype", render_mimetype())
        self.epub.writestr("META-INF/container.xml", render_container_xml())
        self.epub.writestr(
            "item/standard.opf",
            render_standard_opf(
                uuid=self.epubid,
                title=self.title,
                subjects=self.subjects,
                authors=self.authors,
                publisher=self.publisher,
                language=self.language,
                updated_date=self.updated_date,
                view_width=self.view_width,
                view_height=self.view_height,
                reading_order=self.reading_order,
                manifest_images=self.manifest_images,
                manifest_xhtmls=self.manifest_xhtmls,
                manifest_spines=self.manifest_spines,
            ))
        self.epub.writestr(
            "item/navigation-documents.xhtml",
            render_navigation_documents_xhtml(
                title=self.nav_title,
                nav_items=self.nav_items,
            ))
        self.epub.writestr("item/style/fixed-layout-jp.css", get_fixed_layout_jp_css())

        self.__close()
