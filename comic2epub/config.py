import toml
from dataclasses import dataclass


@dataclass(eq=False)
class MyConfig:
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
    manual_title_format: str = r"{title}-{index}"
    # fixed split
    fixed_split: int = -1
    fixed_replace_cover: bool = False
    fixed_title_format: str = r"{title}-{index}"
    # filter
    min_chapters: int = -1
    min_pages: int = -1
    min_pages_ratio: float = 1.0
    max_pages: int = -1
    # others
    logging_path: str = './logs'
    output_path: str = './epubs'
    source_path: str = './raw'

    def parse_file(self, path: str):
        cfg = toml.load(path)
        for dic in cfg.values():
            self.__dict__.update(dic)
