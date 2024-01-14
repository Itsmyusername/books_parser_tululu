import argparse
import json
import posixpath
import urllib
from pathlib import Path

import pathvalidate
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BOOK_CATEGORY = 'https://tululu.org/l55/'
VHOST = 'https://tululu.org'
BOOK_DOWNLOAD_PATTERN = 'https://tululu.org/txt.php'
BOOK_PAGE_PATTERN = 'https://tululu.org/b'
IMAGES_FOLDER = 'images'
BOOKS_FOLDER = 'books'


def main():
    catalogue = []
    last_page = get_last_category_page(BOOK_CATEGORY)

    parser = argparse.ArgumentParser(description='Этот скрипт скачает книги и изображения')
    parser.add_argument('--start_page', type=int, default=1, help='Начальная страница')
    parser.add_argument('--end_page', type=int, default=last_page + 1, help='Страница, перед которой остановить парсинг')
    args = parser.parse_args()

    for page_number in range(args.start_page, args.end_page):
        book_category_paginated = urllib.parse.urljoin(BOOK_CATEGORY, str(page_number))
        response = requests.get(book_category_paginated, verify=False)
        try:
            response.raise_for_status()
            pars_books_from_page(response, catalogue)
        except requests.exceptions.HTTPError as err:
            pass

    write_books_meta_to_json(catalogue)


def write_books_meta_to_json(books_meta_raw):
    with open('books.json', 'w', encoding='UTF-8') as json_file:
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
    if response.history:
        print("Redirect detected")
        response = requests.get(response.url, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    h1_text = soup.select_one('body h1').text
    title, author = h1_text.split('::')
    pic_url = soup.select_one('.bookimage img')['src']
    comments = [comment.text for comment in soup.select('.ow_px_td .black')]
    genres = [genre.text for genre in soup.select('.ow_px_td span.d_book a')]
    book_info = {
        'title': pathvalidate.sanitize_filename(title.strip()),
        'author': author.strip(),
        'img_src': '',
        'book_path': '',
        'comments': comments,
        'genres': genres
    }
    return book_info, pic_url


def pars_books_from_page(response, catalogue):
    soup = BeautifulSoup(response.text, features='lxml')
    selector = '.ow_px_td .bookimage a'
    books_listing_raw = soup.select(selector)
    for book_tag in books_listing_raw:
        book_id = book_tag['href'].strip('/b')
        book_info, pic_url = parse_book_page(book_id)
        book_path = download_txt(book_id, book_info["title"])
        book_info['book_path'] = book_path
        if book_path:
            img_src = download_image(pic_url)
            book_info['img_src'] = img_src
            catalogue.append(book_info)


def download_txt(book_id, book_title):
    payload = {'id': book_id}
    response = requests.get(BOOK_DOWNLOAD_PATTERN, params=payload, verify=False)
    response.raise_for_status()
    if response.url == 'https://tululu.org/':
        raise ValueError(f"Unexpected redirect or invalid book ID: {book_id}")
    try:
        txt_full_path = posixpath.join(BOOKS_FOLDER, '')
        Path(txt_full_path).mkdir(parents=True, exist_ok=True)
        filename = f'{txt_full_path}{book_title}.txt'
    except OSError as e:
        raise OSError(f"Error creating directory or file path: {e}")
    try:
        with open(filename, 'w', encoding='UTF-8') as book:
            book.write(response.text)
    except IOError as e:
        raise IOError(f"Error writing to file: {e}")
    return posixpath.join(txt_full_path, f'{book_title}.txt')


def download_image(img_relative_src):
    pic_absolute_url = urllib.parse.urljoin(VHOST, img_relative_src)
    response = requests.get(pic_absolute_url, verify=False)
    response.raise_for_status()
    image_full_path = posixpath.join(IMAGES_FOLDER, '')
    Path(image_full_path).mkdir(parents=True, exist_ok=True)
    img_name = posixpath.basename(pic_absolute_url)
    with open(f'{image_full_path}{img_name}', 'wb') as img:
        img.write(response.content)
    img_src = posixpath.join(image_full_path, img_name)
    return img_src


if __name__ == '__main__':
    main()
