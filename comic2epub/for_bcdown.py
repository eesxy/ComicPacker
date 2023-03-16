import os
import toml
import natsort
from ._comicepub import ComicEpub
from .utils.utils import safe_makedirs, setup_logger, read_img
from .utils.filter import comic_filter
from .utils.config import MyConfig
from .utils.const import IMAGE_EXT


def convert(cfg: MyConfig):
    assert cfg.source_format == 'bcdown'

    safe_makedirs(cfg.logging_path)
    safe_makedirs(cfg.output_path)
    logger = setup_logger(cfg.logging_path)

    # filter
    comic_names = os.listdir(cfg.source_path)
    filtered_comics = comic_filter(
        cfg.source_path,
        comic_names,
        min_chapters=cfg.min_chapters,
        min_pages=cfg.min_pages,
        min_pages_ratio=cfg.min_pages_ratio,
        max_pages=cfg.max_pages,
        logger=logger,
    )

    for comic, chapters in filtered_comics.items():
        comic_path = os.path.join(cfg.source_path, comic)
        meta_path = os.path.join(comic_path, 'meta.toml')
        if not os.path.exists(meta_path):
            logger.warning(f'Ignored comic {comic}: missing meta.toml')
        meta = toml.load(meta_path)
        # comic name
        comic = meta['title']
        epub = ComicEpub(
            os.path.join(cfg.output_path, comic),
            title=(comic, comic),
            view_height=cfg.view_height,
            view_width=cfg.view_width,
            reading_order=cfg.reading_order,
        )
        
        # cover
        cover_path = os.path.join(comic_path, 'cover.jpg')
        if os.path.exists(cover_path):
            data = read_img(cover_path)
            epub.add_comic_page(data, '.jpg', page='cover', cover=True)
        else:
            logger.debug(f'Cover not exist: {comic}')
        # chapters
        for chapter in chapters:
            chapter_path = os.path.join(comic_path, chapter)
            meta_path = os.path.join(chapter_path, 'meta.toml')
            if not os.path.exists(meta_path):
                logger.warning(f'Ignored chapter {chapter} in {comic}: missing meta.toml')
            meta = toml.load(meta_path)
            chapter = meta['title']
            imgs = meta['paths']

            navigation = True
            index = 0
            for img in imgs:
                img = os.path.split(img)[1]
                ext = os.path.splitext(img)[1]
                if not ext in IMAGE_EXT:
                    logger.debug(f'Not a image: {img} in {chapter}, {comic}')
                data = read_img(os.path.join(chapter_path, img))
                if cfg.rearrangement:
                    epub.add_comic_page(data, ext, cover=False,
                                        nav_label=(chapter if navigation else None))
                else:
                    epub.add_comic_page(data, ext, chapter, '{:04d}'.format(index), cover=False,
                                        nav_label=(chapter if navigation else None))
                navigation = False
                index += 1
        epub.save()
        logger.info(f'Converted {comic}')


if __name__ == '__main__':
    convert(MyConfig('../settings.cfg'))
