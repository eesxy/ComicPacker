import configparser


class MyConfig:
    def __init__(self, cfg_path) -> None:
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path, encoding="utf-8")
        # format
        self.source_format = cfg.get('format', 'SOURCE_FORMAT')
        # epub
        self.view_height = cfg.getint('epub', 'VIEW_HEIGHT')
        self.view_width = cfg.getint('epub', 'VIEW_WIDTH')
        self.reading_order = cfg.get('epub', 'READING_ORDER')
        self.rearrangement = cfg.getboolean('epub', 'REARRANGEMENT')
        # filter
        self.min_chapters = cfg.getint('filter', 'MIN_CHAPTERS')
        self.min_pages = cfg.getint('filter', 'MIN_PAGES')
        self.min_pages_ratio = cfg.getfloat('filter', 'MIN_PAGES_RATIO')
        self.max_pages = cfg.getint('filter', 'MAX_PAGES')
        # others
        self.logging_path = cfg.get('others', 'LOGGING_PATH')
        self.output_path = cfg.get('others', 'OUTPUT_PATH')
        self.source_path = cfg.get('others', 'SOURCE_PATH')
