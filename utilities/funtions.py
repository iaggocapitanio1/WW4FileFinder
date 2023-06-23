import logging.config
import re
from pathlib import Path
from typing import Union, Optional

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
    """
        Verifies if the given source_path contains the specified reference directory
        and that the source_path is a file located under the reference directory.

        Parameters:
        - source_path (Path): The path of the file to be verified.
        - reference (str): The reference directory to check if source_path is under. Default is 'Lists_and_Tags'.

        Returns:
        - bool: True if source_path is a file and is under the reference directory, False otherwise.
        """
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


def get_valid_filename(name):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s)
    if s in {'', '.', '..'}:
        raise ValueError("Could not derive file name from '%s'" % name)
    return s
