import toml
from dataclasses import dataclass


@dataclass(eq=False)
class MyConfig:
    # path
    logging_path: str = './logs'
    output_path: str = './epubs'
    source_path: str = './raw'
    # format
    source_format: str = "general"
    # epub
    view_height: int = 1200
    view_width: int = 848
    reading_order: str = "ltr"
    rearrangement: bool = False
    # manual split
    manual_split: str = ""
    manual_replace_cover: bool = False
    manual_separate_folder: bool = False
    manual_title_format: str = r"{title}-{index}"
    # fixed split
    fixed_split: int = -1
    fixed_replace_cover: bool = False
    fixed_separate_folder: bool = False
    fixed_title_format: str = r"{title}-{index}"
    # comic filter
    min_chapters: int = -1
    min_pages: int = -1
    min_pages_ratio: float = 1.0
    # chapter filter
    max_pages: int = -1
    # dedup
    enable_dedup: bool = False
    dedup_method: str = 'phash'
    # image pipeline
    enable_image_pipeline = False
    fixed_ext = ""
    jpeg_quality = 95
    png_compression = 1
    # crop
    enable_crop: bool = False
    crop_lower_threshold: int = 0
    crop_upper_threshold: int = 255
    # downsample
    enable_downsample = False
    screen_height = 1680
    screen_width = 1264
    interpolation = "area"

    def parse_file(self, path: str):
        cfg = toml.load(path)
        for dic in cfg.values():
            self.__dict__.update(dic)
