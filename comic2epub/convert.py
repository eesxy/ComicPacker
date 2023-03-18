import os
import toml
from tqdm import tqdm
from typing import Dict, List
from ._comicepub import ComicEpub
from .config import MyConfig
from .utils import safe_makedirs, setup_logger, read_img
from .parser import GeneralParser, TachiyomiParser, BcdownParser
from .filter import ComicFilter, ChapterFilter
from .split import fixed_split, manual_split
from .image_pipeline import ImagePipeline, ThresholdCrop, DownSample


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

    # filter
    comic_filter = ComicFilter(cfg.min_chapters, cfg.min_pages, cfg.min_pages_ratio, logger)
    chapter_filter = ChapterFilter(cfg.max_pages, logger)

    # manual split
    manual_breakpoints: Dict[str, List] = {}
    if cfg.manual_split != '':
        meta = toml.load(cfg.manual_split)
        for dic in meta.values():
            manual_breakpoints[dic['title']] = dic['breakpoints']

    # image pipeline
    image_pipeline = ImagePipeline(cfg.fixed_ext, cfg.jpeg_quality, cfg.png_compression)
    if cfg.enable_crop:
        image_pipeline.append(ThresholdCrop(cfg.crop_lower_threshold, cfg.crop_upper_threshold))
    if cfg.enable_downsample:
        image_pipeline.append(DownSample(cfg.screen_height, cfg.screen_width, cfg.interpolation))

    for comic_folder in os.listdir(cfg.source_path):
        path = os.path.join(cfg.source_path, comic_folder)
        if not os.path.isdir(path): continue
        # parse
        comic = parser.parse(path)
        # filter
        if not comic_filter.filt(comic): continue
        chapter_filter.filt(comic)
        # split
        if comic.title in manual_breakpoints:
            comics = manual_split(
                comic,
                manual_breakpoints[comic.title],
                cfg.manual_replace_cover,
                cfg.manual_title_format,
            )
            split = True
        elif cfg.fixed_split != -1:
            comics = fixed_split(
                comic,
                cfg.fixed_split,
                cfg.fixed_replace_cover,
                cfg.fixed_title_format,
            )
            split = True
        else:
            comics = [comic]
            split = False
        original_title = comic.title
        for comic in tqdm(comics, desc='comics  ', position=0):
            if split:
                filefolder = os.path.join(cfg.output_path, original_title)
                safe_makedirs(filefolder)
                filename = os.path.join(filefolder, comic.title + '.epub')
            else:
                filename = os.path.join(cfg.output_path, original_title + '.epub')
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
            for chapter in tqdm(comic.chapters, desc='chapters', position=1, leave=False):
                for index, page in enumerate(
                        tqdm(chapter.pages, desc='pages   ', position=2, leave=False)):
                    data, ext = read_img(page.path)
                    if cfg.enable_image_pipeline:
                        data, ext = image_pipeline(data, ext)
                    epub.add_comic_page(data, ext, chapter.title, page.title,
                                        nav_label=(chapter.title if index == 0 else None))
            epub.save()
        logger.info(f'Converted {original_title}')


if __name__ == '__main__':
    convert(MyConfig())
