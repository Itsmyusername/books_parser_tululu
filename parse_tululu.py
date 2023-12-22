import argparse
import json
import logging
import posixpath
import urllib
from pathlib import Path

import pathvalidate
import requests
import urllib3
from bs4 import BeautifulSoup

logger = logging.getLogger('parse_lululu')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BOOK_CATEGORY = 'https://tululu.org/l55/'
VHOST = 'https://tululu.org'
BOOK_DOWNLOAD_PATTERN = 'https://tululu.org/txt.php'
BOOK_PAGE_PATTERN = 'https://tululu.org/b'
IMAGES_FOLDER = 'images'
BOOKS_FOLDER = 'books'


def main():
    logging.basicConfig(level=logging.INFO)
    catalogue = []
    last_page = get_last_category_page(BOOK_CATEGORY)

    parser = argparse.ArgumentParser(
        description='Этот скрипт скачает книги и изображения')
    parser.add_argument('--start_page', type=int,
                        default=1,
                        help='Начальная страница', )
    parser.add_argument('--end_page', type=int,
                        default=last_page + 1,
                        help='Страница, перед которой остановить парсинг', )
    parser.add_argument('--dest_folder',
                        default='',
                        help='Путь к каталогу с результатами парсинга')
    parser.add_argument('--skip_imgs', action='store_true',
                        help='не скачивать картинки', )
    parser.add_argument('--skip_txt', action='store_true',
                        help='не скачивать книги', )
    parser.add_argument('--json_path',
                        default='',
                        help='указать свой путь к *.json файлу с результатами', )
    args = parser.parse_args()
    logger.info(args)
    for page_number in range(args.start_page, args.end_page):
        book_category_paginated = urllib.parse.urljoin(BOOK_CATEGORY,
                                                       str(page_number))
        response = requests.get(book_category_paginated, verify=False)
        try:
            response.raise_for_status()
            logger.info(f'Начинаю парсить страницу = {page_number}')
            pars_books_from_page(response,
                                 args.dest_folder,
                                 args.skip_imgs,
                                 args.skip_txt,
                                 catalogue
                                 )
        except requests.exceptions.HTTPError as err:
            logger.warning(err)
    write_books_meta_to_json(catalogue, args.dest_folder, args.json_path)


def write_books_meta_to_json(books_meta_raw, base_save_path, json_path):
    full_path = posixpath.join(base_save_path, json_path, '')
    Path(full_path).mkdir(parents=True, exist_ok=True)
    with open(f'{full_path}books.json', 'w', encoding='UTF-8') as json_file:
        json.dump(books_meta_raw, json_file, ensure_ascii=False, indent=2)


def get_last_category_page(category_url):
    response = requests.get(category_url)
    soup = BeautifulSoup(response.text, 'lxml')
    selector = '.center a:last-of-type'
    last_page = soup.select_one(selector).text
    return int(last_page)


def parse_book_page(book_id):
    book_url = f'{BOOK_PAGE_PATTERN}{book_id}'
    response = requests.get(book_url, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    h1_text = soup.select_one('body h1').text
    title, author = h1_text.split('::')
    pic_url = soup.select_one('.bookimage img')['src']
    comments = [comment.text for comment in soup.select('.ow_px_td .black')]
    genres = [genre.text for genre in soup.select('.ow_px_td span.d_book a')]
    book_meta_info = {
        'title': pathvalidate.sanitize_filename(title.strip()),
        'author': author.strip(),
        'img_src': '',
        'book_path': '',
        'comments': comments,
        'genres': genres
    }
    return book_meta_info, pic_url


def pars_books_from_page(response, base_save_path, skip_imgs, skip_txt,
                         catalogue):
    soup = BeautifulSoup(response.text, features='lxml')
    selector = '.ow_px_td .bookimage a'
    books_listing_raw = soup.select(selector)
    for book_tag in books_listing_raw:
        book_id = book_tag['href'].strip('/b')
        book_meta_info, pic_url = parse_book_page(book_id)
        book_path = download_txt(book_id,
                                 base_save_path,
                                 skip_txt,
                                 book_meta_info["title"]
                                 )
        book_meta_info['book_path'] = book_path
        if book_path:
            img_src = download_image(pic_url,
                                     base_save_path,
                                     skip_imgs
                                     )
            book_meta_info['img_src'] = img_src
            catalogue.append(book_meta_info)


def download_txt(book_id, base_save_path, skip_txt, book_title):
    """Функция для скачивания текстовых файлов.

    Args:
        book_id (int): Ссылка на id книги, которую хочется скачать.
        # book_meta_info (dict): Словарь метаданных о книге.
        base_save_path (str): Путь к каталогу с папкой books
        skip_txt (bool): Если True, то пропустить скачивание текста
        book_title(str): Название книги
    Returns:
        None
    """
    payload = {'id': book_id}
    response = requests.get(BOOK_DOWNLOAD_PATTERN, params=payload, verify=False)
    response.raise_for_status()
    if not response.url == 'https://tululu.org/' and not skip_txt:
        txt_full_path = posixpath.join(base_save_path, BOOKS_FOLDER, '')
        Path(txt_full_path).mkdir(parents=True, exist_ok=True)
        filename = f'{txt_full_path}{book_title}.txt'
        with open(filename, 'w', encoding='UTF-8') as book:
            book.write(response.text)
        book_path = posixpath.join(txt_full_path,
                                   f'{book_title}.txt')
        # book_meta_info['book_path'] = book_path
        logger.info(f'Книга скачана id={book_id}')
        return book_path
    logger.warning(f'Ошибка скачивания книги id={book_id}')


def download_image(img_relative_src, base_save_path, skip_imgs):
    if not skip_imgs:
        pic_absolute_url = urllib.parse.urljoin(VHOST, img_relative_src)
        response = requests.get(pic_absolute_url, verify=False)
        response.raise_for_status()
        image_full_path = posixpath.join(base_save_path, IMAGES_FOLDER, '')
        Path(image_full_path).mkdir(parents=True, exist_ok=True)
        img_name = posixpath.basename(pic_absolute_url)
        with open(f'{image_full_path}{img_name}', 'wb') as img:
            img.write(response.content)
        img_src = posixpath.join(image_full_path, img_name)
        return img_src


if __name__ == '__main__':
    main()
