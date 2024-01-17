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

    for book_id in range(args.start_id, args.end_id + 1):
        book_url = f'{BOOK_PAGE_PATTERN}{book_id}'
        try:
            html_content = get_html(book_url)
            book_details = parse_book_page(html_content, book_id)
            book_path = download_txt(str(book_id), book_details["title"])
            book_details['book_path'] = book_path
            if book_path:
                img_src = download_image(book_details['img_src'])
                book_details['img_src'] = img_src
        except requests.exceptions.HTTPError as err:
            print(f"Не удалось скачать книгу с ID {book_id}: {err}")
            continue



def get_html(url):
    response = session.get(url, verify=False)
    response.raise_for_status()
    return response.text


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

session = create_session() 


def parse_book_page(html_content, book_id):
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
        pic_url = img_tag['src']
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


def get_book_page(book_id):
    book_url = f'{BOOK_PAGE_PATTERN}{book_id}'
    response = requests.get(book_url, verify=False)
    response.raise_for_status()
    return response.text


def pars_books_from_page(response, catalogue):
    soup = BeautifulSoup(response.text, features='lxml')
    selector = '.ow_px_td .bookimage a'
    books_listing_raw = soup.select(selector)
    for book_tag in books_listing_raw:
        book_id = book_tag['href'].strip('/b')
        book_details, pic_url = parse_book_page(book_id)
        book_path = download_txt(book_id, book_details["title"])
        book_details['book_path'] = book_path
        if book_path:
            img_src = download_image(pic_url)
            book_details['img_src'] = img_src
            catalogue.append(book_details)


def download_txt(book_id, book_title):
    payload = {'id': book_id}
    response = requests.get(BOOK_DOWNLOAD_PATTERN, params=payload, verify=False)
    response.raise_for_status()
    if response.url == 'https://tululu.org/':
        print(f"Redirect detected or invalid book ID: {book_id}")
        return None  # Возвращаем None или путь к файлу-заглушке
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
