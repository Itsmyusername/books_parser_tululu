logger_config = {
    'version': 1,
    'formatters': {
        'std_format': {
            'format': '{asctime} - {levelname} - {name} - {message}',
            'style': '{',
            },
        },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'book_parser.log',
            'mode': 'a',
            'formatter': 'std_format',
            'level': 'DEBUG',
            },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'std_format',
            'level': 'ERROR',
        },
        },
    'loggers': {
        'parse_tululu_category_logger': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
        'parse_tululu_logger': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
    },
}
