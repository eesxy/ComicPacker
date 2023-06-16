import os
import toml
import logging
import natsort
from typing import Dict, List, Tuple
from multiprocessing import Pool
from ._comicepub import ComicEpub
from .comiccbz import ComicCbz
from .config import MyConfig
from .comic import Comic
from .utils import safe_makedirs, setup_logger, read_img
from .parser import GeneralParser, TachiyomiParser, BcdownParser, DmzjBackupParser
from .split import fixed_split, manual_split
from .comic_pipeline import ComicFilter, ChapterFilter, ImageDedup, ComicFilterPipeline, ComicProcessPipeline
from .image_pipeline import ImagePipeline, ThresholdCrop, DownSample


def pack_epub(
    filename: str,
    comic: Comic,
    comic_processing: ComicProcessPipeline,
    image_pipeline: ImagePipeline,
    cfg: MyConfig,
):
    comic = comic_processing(comic)
    epub = ComicEpub(
        filename,
        title=(comic.title, comic.title),
        subjects=comic.subjects,
        authors=(None if (comic.authors is None) else [(a, a) for a in comic.authors]),
        description=comic.description,
        view_width=cfg.view_width,
        view_height=cfg.view_height,
        reading_order=cfg.reading_order,
    )
    errls = []
    if comic.cover_path is not None:
        data, ext = read_img(comic.cover_path)
        try:
            if cfg.enable_image_pipeline:
                data, ext = image_pipeline(data, ext)
            epub.add_comic_page(data, ext, page='cover', cover=True)
        except UserWarning as e:
            errls.append(str(e) + f': cover in {comic.title}')
    for chapter_index, chapter in enumerate(comic.chapters):
        for page_index, page in enumerate(chapter.pages):
            data, ext = read_img(page.path)
            try:
                if cfg.enable_image_pipeline:
                    data, ext = image_pipeline(data, ext)
                epub.add_comic_page(
                    data, ext, cfg.chapter_format.format(title=chapter.title, index=chapter_index),
                    cfg.page_format.format(title=page.title, index=page_index),
                    nav_label=(chapter.title if page_index == 0 else None))
            except UserWarning as e:
                errls.append(str(e) + f': {page.title} in {chapter.title} {comic.title}')
    epub.save()
    return os.path.split(filename)[1], errls


def pack_cbz(
    filename: str,
    comic: Comic,
    comic_processing: ComicProcessPipeline,
    image_pipeline: ImagePipeline,
    cfg: MyConfig,
):
    comic = comic_processing(comic)
    cbz = ComicCbz(
        filename,
        title=comic.title,
        writer=(None if (comic.authors is None) else ','.join(comic.authors)),
        publisher=comic.publisher,
        genre=(None if (comic.subjects is None) else ','.join(comic.subjects)),
        summary=comic.description,
    )
    errls = []
    if comic.cover_path is not None:
        data, ext = read_img(comic.cover_path)
        try:
            if cfg.enable_image_pipeline:
                data, ext = image_pipeline(data, ext)
            cbz.add_comic_page(data, ext, '000-cover', 'cover')
        except UserWarning as e:
            errls.append(str(e) + f': cover in {comic.title}')
    for chapter_index, chapter in enumerate(comic.chapters):
        for page_index, page in enumerate(chapter.pages):
            data, ext = read_img(page.path)
            try:
                if cfg.enable_image_pipeline:
                    data, ext = image_pipeline(data, ext)
                cbz.add_comic_page(
                    data, ext, cfg.chapter_format.format(title=chapter.title, index=chapter_index),
                    cfg.page_format.format(title=page.title, index=page_index),
                    nav_label=(chapter.title if page_index == 0 else None))
            except UserWarning as e:
                errls.append(str(e) + f': {page.title} in {chapter.title} {comic.title}')
    cbz.save()
    return os.path.split(filename)[1], errls


def callback(x: Tuple[str, List[str]]):
    logger = logging.getLogger('main')
    filename, errls = x
    logger.info(f'Packed {filename}')
    for err in errls:
        logger.warning(err)
    return


def errback(e: BaseException):
    logger = logging.getLogger('main')
    logger.error(str(e))
    return


def convert(cfg: MyConfig):
    if cfg.source_format == 'general':
        parser = GeneralParser
    elif cfg.source_format == 'tachiyomi':
        parser = TachiyomiParser
    elif cfg.source_format == 'bcdown':
        parser = BcdownParser
    elif cfg.source_format == 'dmzjbackup':
        parser = DmzjBackupParser
    else:
        raise ValueError(f'Invalid source format: {cfg.source_format}')

    safe_makedirs(cfg.logging_path)
    safe_makedirs(cfg.output_path)
    logger = setup_logger(cfg.logging_path)

    # comic pipeline
    comic_filter = ComicFilterPipeline(
        ComicFilter(cfg.min_chapters, cfg.min_pages, cfg.min_pages_ratio, cfg.min_total_pages),
        ChapterFilter(cfg.max_pages),
    )
    comic_processing = ComicProcessPipeline()
    if cfg.enable_dedup:
        comic_processing.append(ImageDedup(cfg.dedup_method))

    # manual split
    manual_breakpoints: Dict[str, List] = {}
    manual_replace_cover: Dict[str, bool] = {}
    if cfg.manual_split != '':
        meta = toml.load(cfg.manual_split)
        for dic in meta.values():
            manual_breakpoints[dic['title']] = dic['breakpoints']
            manual_replace_cover[dic['title']] = cfg.manual_replace_cover
            if 'replace_cover' in dic:
                manual_replace_cover[dic['title']] = dic['replace_cover']

    # image pipeline
    image_pipeline = ImagePipeline(cfg.fixed_ext, cfg.jpeg_quality, cfg.png_compression)
    if cfg.enable_crop:
        image_pipeline.append(ThresholdCrop(cfg.crop_lower_threshold, cfg.crop_upper_threshold))
    if cfg.enable_downsample:
        image_pipeline.append(DownSample(cfg.screen_height, cfg.screen_width, cfg.interpolation))

    pool = Pool()

    for comic_folder in natsort.os_sorted(os.listdir(cfg.source_path)):
        path = os.path.join(cfg.source_path, comic_folder)
        if not os.path.isdir(path): continue
        # parse
        comic = parser.parse(path)
        # split
        if comic.title in manual_breakpoints:
            comics = manual_split(
                comic,
                manual_breakpoints[comic.title],
                manual_replace_cover[comic.title],
                cfg.manual_title_format,
            )
            split = cfg.manual_separate_folder
        elif cfg.fixed_split != -1:
            comics = fixed_split(
                comic,
                cfg.fixed_split,
                cfg.fixed_replace_cover,
                cfg.fixed_title_format,
            )
            split = cfg.fixed_separate_folder
        else:
            comics = [comic]
            split = False
        original_title = comic.title
        for comic in comics:
            if split:
                filefolder = os.path.join(cfg.output_path, original_title)
                safe_makedirs(filefolder)
                filename = os.path.join(filefolder, comic.title + '.' + cfg.output_format)
            else:
                filename = os.path.join(cfg.output_path, comic.title + '.' + cfg.output_format)
            if os.path.exists(filename):
                logger.info(f'{os.path.split(filename)[1]} exists')
                continue
            if not comic_filter(comic): continue
            # logger.info(f'Packing {os.path.split(filename)[1]}')
            if cfg.output_format == 'epub':
                pool.apply_async(pack_epub,
                                 (filename, comic, comic_processing, image_pipeline, cfg),
                                 callback=callback, error_callback=errback)
            elif cfg.output_format == 'cbz':
                pool.apply_async(pack_cbz, (filename, comic, comic_processing, image_pipeline, cfg),
                                 callback=callback, error_callback=errback)
            else:
                raise ValueError('Invalid output format ' + cfg.output_format)

    pool.close()
    pool.join()


if __name__ == '__main__':
    convert(MyConfig())
