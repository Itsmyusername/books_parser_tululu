import json
import logging.config
import os
from time import sleep
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

from config import logger_config

logger = logging.getLogger("parse_tululu_logger")


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_txt(book_id, filename, folder, timeout=10):
    url = "https://tululu.org/txt.php"
    payload = {'id': book_id}

    response = requests.get(url, params=payload, timeout=timeout)
    response.raise_for_status()

    check_for_redirect(response)

    book = response.text

    os.makedirs(folder, exist_ok=True)

    filename = ". ".join([str(book_id), sanitize_filename(filename)])
    book_path = os.path.join(folder, ".".join([filename, 'txt']))

    with open(book_path, 'w') as file:
        file.write(book)


def download_image(url, folder, timeout=10):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    check_for_redirect(response)

    _, image_filename = os.path.split(urlsplit(url).path)

    os.makedirs(folder, exist_ok=True)

    image_path = os.path.join(folder, image_filename)

    with open(image_path, 'wb') as file:
        file.write(response.content)


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.select_one('h1')

    book_name = title_tag.text.split('::')[0].strip()
    book_author = title_tag.text.split('::')[1].strip()

    image_src = soup.select_one('.bookimage img')['src']
    book_image_url = urljoin(response.url, image_src)

    book_genres = [genre.text for genre in soup.select('span.d_book a')]

    book_comments = [comment.text for comment in soup.select('.texts span')]

    book_details = {
        'name': book_name,
        'author': book_author,
        'image_url': book_image_url,
        'image_src': os.path.join('images', image_src.split('/')[-1]),
        'genres': book_genres,
        'comments': book_comments,
    }

    return book_details


def get_books_by_ids(ids, dest_folder, skip_imgs=False, skip_txt=False):
    logging.config.dictConfig(logger_config)
    logger.debug('Start parsing books')

    current_book_id_index = 0
    timeout = 10

    books_details = []

    while current_book_id_index < len(ids):
        current_book_id = ids[current_book_id_index]
        logger.debug(f'Start while, trу to download book with ID {current_book_id} (index {current_book_id_index})')
        try:
            url = f'https://tululu.org/b{current_book_id}/'
            book_page = requests.get(url, timeout=timeout)
            book_page.raise_for_status()

            check_for_redirect(book_page)

            book_details = parse_book_page(book_page)
            if not skip_txt:
                books_path = os.path.join(dest_folder, 'books')
                download_txt(current_book_id, book_details['name'], books_path, timeout)
            if not skip_imgs:
                images_path = os.path.join(dest_folder, 'images')
                download_image(book_details['image_url'], images_path, timeout)
            books_details.append(book_details)
            logger.debug('Book was downloaded')
        except requests.exceptions.HTTPError:
            logger.error(f'Book with ID {current_book_id} is not found')
            current_book_id_index += 1
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            logger.error('Connection error')
            sleep(5)
        else:
            current_book_id_index += 1
            print('Название:', book_details['name'])
            print('Автор:', book_details['author'])
            print('')

    os.makedirs(dest_folder, exist_ok=True)
    json_file_path = os.path.join(dest_folder, 'books_details.json')

    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(books_details, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    get_books_by_ids([1, 2])
