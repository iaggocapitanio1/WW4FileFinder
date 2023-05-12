import logging.config
from functools import wraps
from pathlib import Path
from typing import Union

import settings
from utilities.funtions import get_budget_name, get_email

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)


def validate_on_folder_input(func):
    @wraps(func)
    def wrapper(src_path: Union[str, Path], *args, **kwargs):
        paths = [src_path.__str__()]
        dest_path = kwargs.get('dest_path')
        if dest_path:
            paths.append(dest_path.__str__())

        for path in paths:
            if settings.PATH_REFERENCE not in path:
                logger.error(f"The provided path '{path}' is deemed invalid! It must include the requisite reference: "
                             f"{settings.PATH_REFERENCE}.")
                return False
            email = get_email(path)
            budget = get_budget_name(path)
            if not email:
                logger.error(f"User email not found in path: {path}!")
                return False
            if not budget:
                logger.error(f"User budget not found in path: {path}!")
                return False
        return func(src_path, *args, **kwargs)

    return wrapper
