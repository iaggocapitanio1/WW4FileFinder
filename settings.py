from pathlib import Path
from dotenv import load_dotenv
import os

import logging

logger = logging.getLogger(__name__)


def str_to_bool(target) -> bool:
    if isinstance(target, bool):
        return target
    return target.lower() == 'true'


def mega_bytes_to_bits(mega: int) -> int:
    return mega * 1024 * 1024


NAMESPACE = 'FILE_FINDER'

if not NAMESPACE.endswith('_'):
    NAMESPACE += '_'


def parse_env(string: str) -> str:
    return NAMESPACE + string


BASE_DIR = Path(__file__).resolve().parent

PRODUCTION = True

DOT_ENV_PATH = BASE_DIR / '.dev.env' if not PRODUCTION else None

load_dotenv(DOT_ENV_PATH)

NUM_WORKER_THREADS = int(os.environ.get(parse_env("NUM_WORKER_THREADS"), 4))

DELAY_FOR_SCAN = int(os.environ.get(parse_env("DELAY_FOR_SCAN"), 20))

SLEEP_DURATION = int(os.environ.get(parse_env("DELAY_FOR_SCAN"), 0.5))

KEY_PATH = os.environ.get(parse_env("KEY_WORD"), "mofreitas")

PATH_REFERENCE = os.environ.get(parse_env("PATH_REFERENCE"), "mofreitas/clientes/")

CLIENT_ID = os.environ.get(parse_env("CLIENT_ID"), "")

logger.info(f"CLIENT_ID: {CLIENT_ID}")

CLIENT_SECRET = os.environ.get(parse_env("CLIENT_SECRET"), "")

logger.info(f"CLIENT_SECRET: {CLIENT_SECRET}")

TOKEN_URL = os.environ.get(parse_env("TOKEN_URL"), "http://localhost:8000/auth/token")

logger.info(f"TOKEN_URL: {TOKEN_URL}")

URL = os.environ.get(parse_env("URL"), "http://127.0.0.1:8000/api/v1")

WATCHING_DIR = os.environ.get(parse_env("WATCHING_DIR"), BASE_DIR / '/home/app/media/public/mofreitas')

WATCHING_DIR = Path(WATCHING_DIR).resolve()

LOG_DIR = BASE_DIR.joinpath('logs')

LOG_DIR.mkdir(exist_ok=True, mode=0o777)

LOGGER = {
    "version": 1,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - level: %(levelname)s - loc: %(name)s - func: %(funcName)s - msg: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR.joinpath('file_finder.log'),
            "level": "DEBUG",
            "maxBytes": 1048574,
            "backupCount": 3,
            "formatter": "simple"
        }
    },
    "loggers": {
        category: {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": True
        }
        for category in ["client", "utilities", "__main__"]
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"],
    }
}
