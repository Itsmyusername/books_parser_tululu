# Парсер книг
Это скрипт Python, который позволяет вам анализировать и загружать книги научной фантастики с
сайта [tululu.org](https://tululu.org/). Он извлекает сведения о книге, загружает книгу в текстовом формате,
и сохраняет изображение обложки книги.

Вы можете скачать книги научной фантастики, указав диапазон страниц с книгами научной фантастики.

Книги будут сохраняться в папке «books», обложки книг — в папке «images».
Вы можете указать папку назначения для этих папок с аргументом `--dest_folder`.
Файл json с информацией о книгах также будет сохранен в папке назначения.
По умолчанию `tululu_books` является папкой назначения.
Вы также можете пропустить загрузку изображений или текстов книг с помощью флагов `--skip_imgs` или `--skip_txt`.
В консоли вы увидите названия и авторов загруженных книг.

## Запуск
Клонируем репозиторий:


Создайте виртуальную среду:
```
python -m venv env
```

Установите необходимые зависимости:
```
pip install -r requirements.txt
```

## Использование
Для разбора и скачивания книг с первых 5 страниц запустите скрипт следующей командой:

```
Python parse_tululu_category.py --start_page 1 --end_page 5
```

Скрипты будут анализировать книги с первых 5 страниц.
Скрипт выведет имена и авторов загруженных книг в консоль.
Книги будут сохранены в папку с книгами, а обложки книг в папку с изображениями.
описание книг будет сохранено в файле book_details.json. Все эти файлы будут сохранены в папке `books`,
которая является папкой назначения по умолчанию.

Вы можете указать папку назначения для книг и изображений с помощью аргумента --dest_folder:

Скрипт будет анализировать книги в пределах указанного диапазона страниц.


**Примечания:**
- Этот скрипт требует активного подключения к Интернету для доступа к
веб-сайту [tululu.org](https://tululu.org/).
- Скрипт не будет скачивать книги, которых нет на сайте, поэтому в папке с книгами вы можете
найти меньше книг, чем указанный диапазон.
- Идентификаторы книг, отсутствующие на сайте, можно найти в файле ```book_parser.log```.