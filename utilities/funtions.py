from pathlib import Path
from typing import Union, Optional
import logging.config

import settings

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)


def validate_path(path: Union[str, Path]) -> Path:
    if isinstance(path, str):
        path = Path(path)
    return path.resolve()


def get_path_after_keyword(path: Union[str, Path], keyword: str = "mofreitas") -> Optional[Path]:
    try:
        logger.info(f"Trying to get reference path after keyword {keyword}: {path}")
        path = validate_path(path)
        path = Path(*path.parts[path.parts.index(keyword):])
        logger.info(f"Extracted the Path: {path}")
        return path
    except Exception as error:
        logger.error(f"Error: Unable to retrieve the relative path. The event may have been triggered outside the "
                     f"reference path. {error}")


def get_email(path: Union[str, Path], keyword: str = "clientes") -> str:
    path = validate_path(path)
    return path.parts[path.parts.index(keyword) + 1]


def get_budget_name(path: Union[str, Path], keyword: str = "clientes") -> str:
    path = validate_path(path)
    return path.parts[path.parts.index(keyword) + 2]


def verify(source_path: Path, reference: str = 'Lists_and_Tags') -> bool:
    if source_path.is_dir():
        return False
    if reference not in source_path.parts:
        return False
    current_path = Path(*source_path.parts[source_path.parts.index(reference):])
    while current_path != current_path.parent:  # Stop when reaching the root directory
        if current_path.name == reference:
            return True
        current_path = current_path.parent

    return False
