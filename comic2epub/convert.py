import os
import toml
import natsort
from typing import Dict, List
from multiprocessing import Pool
from ._comicepub import ComicEpub
from .config import MyConfig
from .comic import Comic
from .utils import safe_makedirs, setup_logger, read_img
from .parser import GeneralParser, TachiyomiParser, BcdownParser
from .split import fixed_split, manual_split
from .comic_pipeline import ComicFilter, ChapterFilter, ImageDedup, ComicFilterPipeline, ComicProcessPipeline
from .image_pipeline import ImagePipeline, ThresholdCrop, DownSample


def pack_epub(
    filename: str,
    comic: Comic,
    comic_processing: ComicFilter,
    image_pipeline:ImagePipeline,
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
    if comic.cover_path is not None:
        data, ext = read_img(comic.cover_path)
        if cfg.enable_image_pipeline:
            data, ext = image_pipeline(data, ext)
        epub.add_comic_page(data, ext, page='cover', cover=True)
    for chapter in comic.chapters:
        for index, page in enumerate(chapter.pages):
            data, ext = read_img(page.path)
            if cfg.enable_image_pipeline:
                data, ext = image_pipeline(data, ext)
            epub.add_comic_page(data, ext, chapter.title, page.title,
                                nav_label=(chapter.title if index == 0 else None))
    epub.save()
    return os.path.split(filename)[1]


def convert(cfg: MyConfig):
    if cfg.source_format == 'general':
        parser = GeneralParser
    elif cfg.source_format == 'tachiyomi':
        parser = TachiyomiParser
    elif cfg.source_format == 'bcdown':
        parser = BcdownParser
    else:
        raise ValueError(f'Invalid source format: {cfg.source_format}')

    safe_makedirs(cfg.logging_path)
    safe_makedirs(cfg.output_path)
    logger = setup_logger(cfg.logging_path)

    # comic pipeline
    comic_filter = ComicFilterPipeline(
        ComicFilter(cfg.min_chapters, cfg.min_pages, cfg.min_pages_ratio, logger),
        ChapterFilter(cfg.max_pages, logger),
    )
    comic_processing = ComicProcessPipeline()
    if cfg.enable_dedup:
        comic_processing.append(ImageDedup(cfg.dedup_method, logger))

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
    image_pipeline = ImagePipeline(logger, cfg.fixed_ext, cfg.jpeg_quality, cfg.png_compression)
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
                pool.apply_async(pack_epub, (filename, comic, comic_processing, image_pipeline, cfg), callback=lambda x: logger.info(f'Packed {x}'))
            else:
                raise ValueError('Invalid output format ' + cfg.output_format)

    pool.close()
    pool.join()


if __name__ == '__main__':
    convert(MyConfig())
