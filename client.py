import logging.config

from requests_auth import OAuth2ClientCredentials, OAuth2, JsonTokenFileCache

import settings
from pathlib import Path

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)

cache_file = Path(settings.BASE_DIR).joinpath('cache.json')

logger.info(f"Verifying credentials in cache '{cache_file.name}' file.")

if not cache_file.is_file():
    cache_file.touch()  # create file
    logger.info(f"{cache_file} created.")
else:
    logger.info(f"{cache_file} already exists.")

OAuth2.token_cache = JsonTokenFileCache(cache_file.__str__())

oauth = OAuth2ClientCredentials(
    client_id=settings.CLIENT_ID,
    client_secret=settings.CLIENT_SECRET,
    token_url=settings.TOKEN_URL,
    scope=["read", "write"]
)
