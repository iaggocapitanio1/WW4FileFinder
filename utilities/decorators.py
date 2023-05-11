import logging.config
from functools import wraps
from pathlib import Path
from typing import Union

import settings
from utilities.funtions import get_budget_name, get_email

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)


def validate_on_folder_created_input(func):
    @wraps(func)
    def wrapper(src_path: Union[str, Path], *args, **kwargs):
        if settings.PATH_REFERENCE not in src_path:
            logger.error("The provided source path is deemed invalid! It must include the requisite reference: "
                         f"{settings.PATH_REFERENCE}.")
            return False
        email = get_email(src_path)
        budget = get_budget_name(src_path)
        if not email:
            logger.error("User email not found!")
            return False
        if not budget:
            logger.error("User budget not found!")
            return False
        return func(src_path, *args, **kwargs)
    return wrapper
