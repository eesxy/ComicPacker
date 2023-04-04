import os
import toml
import natsort
from tqdm import tqdm
from typing import Dict, List
from ._comicepub import ComicEpub
from .config import MyConfig
from .utils import safe_makedirs, setup_logger, read_img
from .parser import GeneralParser, TachiyomiParser, BcdownParser, DmzjBackupParser
from .split import fixed_split, manual_split
from .comic_pipeline import ComicFilter, ChapterFilter, ImageDedup, ComicPipeline
from .image_pipeline import ImagePipeline, ThresholdCrop, DownSample


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
    comic_pipeline = ComicPipeline(
        ComicFilter(cfg.min_chapters, cfg.min_pages, cfg.min_pages_ratio, cfg.min_total_pages),
        ChapterFilter(cfg.max_pages),
    )
    if cfg.enable_dedup:
        comic_pipeline.append(ImageDedup(cfg.dedup_method))

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
                filename = os.path.join(filefolder, comic.title + '.epub')
            else:
                filename = os.path.join(cfg.output_path, comic.title + '.epub')
            if os.path.exists(filename):
                logger.info(f'{os.path.split(filename)[1]} exists')
                continue
            # comic pipeline
            if not comic_pipeline(comic): continue
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
            logger.info(f'Packing {os.path.split(filename)[1]}')
            if comic.cover_path is not None:
                data, ext = read_img(comic.cover_path)
                if cfg.enable_image_pipeline:
                    try:
                        data, ext = image_pipeline(data, ext)
                        epub.add_comic_page(data, ext, page='cover', cover=True)
                    except UserWarning as e:
                        logger.warning(str(e) + f': cover in {comic.title}')
            for chapter in tqdm(comic.chapters, desc='chapters', position=0, leave=False):
                for index, page in enumerate(
                        tqdm(chapter.pages, desc='pages   ', position=1, leave=False)):
                    data, ext = read_img(page.path)
                    if cfg.enable_image_pipeline:
                        try:
                            data, ext = image_pipeline(data, ext)
                            epub.add_comic_page(data, ext, chapter.title, page.title,
                                                nav_label=(chapter.title if index == 0 else None))
                        except UserWarning as e:
                            logger.warning(
                                str(e) + f': {page.title} in {chapter.title} {comic.title}')
            epub.save()


if __name__ == '__main__':
    convert(MyConfig())
