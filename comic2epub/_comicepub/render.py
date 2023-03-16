import os
from jinja2 import Environment
from typing import List, Tuple, Set, Optional


def get_content_from_file(path):
    with open(os.path.join(os.path.dirname(__file__), path), 'r', encoding='utf-8') as f:
        return f.read()


def render_mimetype():
    return get_content_from_file('./template/mimetype')


def render_container_xml():
    return get_content_from_file('./template/container.xml')


def render_standard_opf(
    uuid: str,
    title: Tuple[str, str],
    subjects: Optional[Set[str]],
    authors: Optional[List[Tuple[str, str, str]]],
    publisher: Optional[Tuple[str, str]],
    language: str,
    updated_date: str,
    view_width: int,
    view_height: int,
    reading_order: str,
    manifest_images: List[Tuple[str, str, str, str]],
    manifest_xhtmls: List[Tuple[str, str]],
    manifest_spines: List[str],
) -> str:
    template = get_content_from_file('./template/standard.opf')
    return Environment().from_string(template).render(
        uuid=uuid,
        title=title,
        subjects=subjects,
        authors=authors,
        publisher=publisher,
        language=language,
        updated_date=updated_date,
        view_width=view_width,
        view_height=view_height,
        reading_order=reading_order,
        manifest_images=manifest_images,
        manifest_xhtmls=manifest_xhtmls,
        manifest_spines=manifest_spines,
    )


def render_navigation_documents_xhtml(
    title: str,
    nav_items: List[Tuple[str, str]],
) -> str:
    template = get_content_from_file('./template/navigation-documents.xhtml')
    return Environment().from_string(template).render(
        title=title,
        nav_items=nav_items,
    )


def render_xhtml(
    title: str,
    image_id: str,
    image_ext: str,
    page_name: str,
    view_width: int,
    view_height: int,
    cover: bool = False,
) -> str:
    template = get_content_from_file('./template/p.xhtml')
    return Environment().from_string(template).render(
        title=title,
        image_id=image_id,
        image_ext=image_ext,
        page_name=page_name,
        view_width=view_width,
        view_height=view_height,
        cover=cover,
    )


def get_fixed_layout_jp_css():
    return get_content_from_file('./template/fixed-layout-jp.css')
