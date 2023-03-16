import argparse
from comic2epub import general, for_bcdown
from comic2epub.utils.config import MyConfig

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', dest='config', type=str, default='settings.cfg')

    args = parser.parse_args()

    cfg = MyConfig(args.config)

    if cfg.source_format == 'general':
        general.convert(cfg)
    elif cfg.source_format == 'bcdown':
        for_bcdown.convert(cfg)
    else:
        raise ValueError(f'Invalid source format {cfg.source_format}')

if __name__ == '__main__':
    main()
