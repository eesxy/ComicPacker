from typing import List, Union
from .comic import Chapter, Comic


def int_ord(order: Union[float, int]):
    if isinstance(order, float) and order.is_integer():
        return int(order)
    else:
        return order


def fixed_split(
    comic: Comic,
    num_chapters: int,
    replace_cover: bool = False,
    title_format: str = r'{title} Chapter {first_ord}-{last_ord}',
) -> List[Comic]:
    '''
    split the comic by number of chapters

    :return: list of comics after split

    :param comic: comic to split
    :param num_chapters: num of chapters in a clip
    :param replace_cover: if True, the clips will use its first page as the cover
    :param title_format: format string of the title of the clips
    '''
    assert num_chapters > 0
    comic_list = []
    chapters_list = [
        comic.chapters[i:i + num_chapters] for i in range(0, len(comic.chapters), num_chapters)]
    for index, chapters in enumerate(chapters_list):
        if replace_cover:
            new_cover_path = chapters[0].pages[0].path
        else:
            new_cover_path = comic.cover_path
        new_title = title_format.format(
            title=comic.title,
            index=index + 1,
            first_ord=int_ord(chapters[0].order),
            last_ord=int_ord(chapters[-1].order),
            first_title=chapters[0].title,
            last_title=chapters[-1].title,
        )
        new_comic = Comic(new_title, new_cover_path, chapters)
        comic_list.append(new_comic)
    return comic_list


def manual_split(
    comic: Comic,
    breakpoints: List[float],
    replace_cover: bool = False,
    title_format: str = r'{title} Volume {index}',
) -> List[Comic]:
    '''
    split the comic by break points

    :return: list of comics after split

    :param comic: comic to split
    :param breakpoints: breakpoints
    :param replace_cover: if True, the clips will use its first page as the cover
    :param title_format: format string of the title of the clips
    '''
    assert len(breakpoints) > 0
    comic_list: List[Comic] = []
    chapters_list: List[List[Chapter]] = []
    chapter_list: List[Chapter] = []
    for chapter in comic.chapters:
        if chapter.order in breakpoints and len(chapter_list) != 0:
            chapters_list.append(chapter_list)
            chapter_list = [chapter]
        else:
            chapter_list.append(chapter)
    chapters_list.append(chapter_list)
    for index, chapters in enumerate(chapters_list):
        if replace_cover:
            new_cover_path = chapters[0].pages[0].path
        else:
            new_cover_path = comic.cover_path
        new_title = title_format.format(
            title=comic.title,
            index=index,
            first_ord=int_ord(chapters[0].order),
            last_ord=int_ord(chapters[-1].order),
            first_title=chapters[0].title,
            last_title=chapters[-1].title,
        )
        new_comic = Comic(new_title, new_cover_path, chapters)
        comic_list.append(new_comic)
    return comic_list
