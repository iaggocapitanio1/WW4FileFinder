from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

NUM_WORKER_THREADS = int(os.environ.get("NUM_WORKER_THREADS", 4))


CLIENT_ID = os.environ.get("CLIENT_ID", "")

CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")

TOKEN_URL = os.environ.get("TOKEN_URL", "http://localhost:8000/auth/token")

URL = os.environ.get("URL", "http://127.0.0.1:8000/api/v1")

WATCHING_DIR = os.environ.get("WATCHING_DIR", BASE_DIR / './clientes')

WATCHING_DIR = Path(WATCHING_DIR).resolve()

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
            "filename": "logs/watchdog.log",
            "level": "DEBUG",
            "maxBytes": 1048574,
            "backupCount": 3,
            "formatter": "simple"
        }
    },
    "loggers": {
        "client": {
            "level": "DEBUG",
            "handlers": [
                "console",
                "file"
            ],
            "propagate": True
        },
        "__main__": {
            "level": "INFO",
            "handlers": [
                "console",
                "file"
            ],
            "propagate": True
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": [
            "console",
            "file"
        ],
    }
}
