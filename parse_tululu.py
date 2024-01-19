import argparse
import posixpath
import urllib
from pathlib import Path

import pathvalidate
import requests
import urllib3
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import HTTPError


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
VHOST = 'https://tululu.org'
BOOK_DOWNLOAD_PATTERN = 'https://tululu.org/txt.php'
BOOK_PAGE_PATTERN = 'https://tululu.org/b'
IMAGES_FOLDER = 'images'
BOOKS_FOLDER = 'books'


def main():
    parser = argparse.ArgumentParser(description='Этот скрипт скачает книги по диапазону ID')
    parser.add_argument('--start_id', type=int, required=True, help='ID первой книги для скачивания')
    parser.add_argument('--end_id', type=int, required=True, help='ID последней книги для скачивания')
    args = parser.parse_args()
    session = create_session()

    for book_id in range(args.start_id, args.end_id + 1):
        book_url = f'{BOOK_PAGE_PATTERN}{book_id}'
        try:
            html_content = get_html(book_url, session)
            book_details = parse_book_page(html_content, book_url)
            book_path = download_txt(str(book_id), book_details["title"], session)
            book_details['book_path'] = book_path
            if book_path and book_details['img_src']:
                img_src = download_image(book_details['img_src'], session)
                book_details['img_src'] = img_src
        except requests.exceptions.RequestException as e:
            print(f"Не удалось обработать книгу с ID {book_id}: {e}")
            continue


def get_html(url, session):
    response = session.get(url, verify=False)
    check_for_redirect(response, VHOST)
    response.raise_for_status()
    return response.text


def check_for_redirect(response, home_url):
    if response.url == home_url:
        raise HTTPError(f"Перенаправление на главную страницу: {response.url}")


def create_session(retries=3, backoff_factor=0.3):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def parse_book_page(html_content, book_url):
    soup = BeautifulSoup(html_content, 'lxml')
    h1_text = soup.select_one('body h1').text
    part_of_name_book = h1_text.split('::', 1)
    if len(part_of_name_book) == 2:
        title, author = part_of_name_book
    else:
        title = h1_text
        author = "Неизвестен"
    img_tag = soup.select_one('.bookimage img')
    if img_tag and 'src' in img_tag.attrs:
        pic_url = urllib.parse.urljoin(book_url, img_tag['src'])
    else:
        pic_url = ''
    comments = [comment.text for comment in soup.select('.ow_px_td .black')]
    genres = [genre.text for genre in soup.select('.ow_px_td span.d_book a')]
    book_details = {
        'title': pathvalidate.sanitize_filename(title.strip()),
        'author': author.strip(),
        'img_src': pic_url,
        'book_path': '',
        'comments': comments,
        'genres': genres
    }
    return book_details


def download_txt(book_id, book_title, session):
    filename = f'{book_title}.txt'
    txt_full_path = posixpath.join(BOOKS_FOLDER, filename)
    Path(BOOKS_FOLDER).mkdir(parents=True, exist_ok=True)
    payload = {'id': book_id}
    response = session.get(BOOK_DOWNLOAD_PATTERN, params=payload, verify=False)
    check_for_redirect(response, VHOST)
    response.raise_for_status()
    with open(txt_full_path, 'w', encoding='UTF-8') as book:
        book.write(response.text)
    return txt_full_path


def download_image(img_src, session):
    img_name = posixpath.basename(img_src)
    img_full_path = posixpath.join(IMAGES_FOLDER, img_name)
    Path(IMAGES_FOLDER).mkdir(parents=True, exist_ok=True)
    response = session.get(img_src, verify=False)
    check_for_redirect(response, VHOST)
    response.raise_for_status()
    with open(img_full_path, 'wb') as img:
        img.write(response.content)
    return img_full_path


if __name__ == '__main__':
    main()
