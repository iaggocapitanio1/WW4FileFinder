import json
import logging.config
from pathlib import Path
from typing import Union, Optional, List, Dict, Tuple

import requests
from requests import Response

import settings
from client import oauth
from utilities.funtions import get_path_after_keyword, validate_path, get_email, get_budget_name
from utilities.decorators import validate_on_folder_created_input

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)


def get(relative_url, params=None) -> Response:
    if params is None:
        params = dict()
    url = settings.URL + relative_url
    return requests.get(url, auth=oauth, params=params)


def post(relative_url, params=None, **kwargs) -> Response:
    if params is None:
        params = dict()
    url = settings.URL + relative_url
    return requests.post(url, auth=oauth, params=params, **kwargs)


def patch(relative_url, params=None, **kwargs) -> Response:
    if params is None:
        params = dict()
    url = settings.URL + relative_url
    return requests.patch(url, auth=oauth, params=params, **kwargs)


def create_folder(name: str, budget_id: str, email: str, parent: Optional[str] = None) -> Response:
    payload = json.dumps({
        "folder_name": name,
        "budget": budget_id,
        "parent_folder": parent,
        "email": email
    })
    headers = {
        'Content-Type': 'application/json'
    }
    return post(relative_url='/storages/folder/create_folder_with_email/', data=payload, headers=headers)


def patch_folder(data: dict, **kwargs):
    payload = json.dumps(data)
    headers = {
        'Content-Type': 'application/json'
    }
    return patch(relative_url='/storages/folder/create_folder_with_email/', data=payload, headers=headers)


def folder_already_exists(path: Union[str, Path], is_src_path: bool = True) -> bool:
    if is_src_path:
        path: Path = get_path_after_keyword(path)
    try:
        params = dict(path=path.__str__())
        response: Response = get(relative_url='/storages/folder/', params=params)
        if not response.status_code == 200:
            msg: str = f"Error {response.status_code}: Unable to establish communication with the server."
            logger.error(msg)
            raise requests.RequestException(msg)
        count = response.json().get('count')
        assert isinstance(count, int)
        return count != 0
    except Exception as error:
        logger.error(f"Error: {error}")
    return False


def find_folder(path: Union[str, Path], **kwargs) -> Optional[str]:
    """
    This function attempts to locate a specific folder based on the provided path and optional keyword.

    Args:
    path (Union[str, Path]): The original path where the folder is to be found.
    **kwargs: Arbitrary keyword arguments.
    - is_src_path (bool, optional): If True, the function will get the path after a specified keyword. Default is True.
    - keyword (str, optional): The keyword used to trim the original path if is_src_path is True. Default is
    "mofreitas".

    Returns: List[Optional[str]]: If a folder(s) is found, the function returns a list of folder IDs. If no folder is
    found or an error occurs, an empty list is returned.

    Raises:
    requests.RequestException: If the status code of the server's response is not 200, an exception is raised.

    Notes:
    This function operates in conjunction with the '/storages/folder/' endpoint of the server and is part of a larger
    script that provides functionality for manipulating folders within a storage system.
    """
    is_src_path: bool = kwargs.get('is_src_path', True)
    keyword: str = kwargs.get('keyword', "mofreitas")
    if is_src_path:
        path: Path = get_path_after_keyword(path, keyword=keyword)
    try:
        params: dict = dict(path=path.__str__())
        response: Response = get(relative_url='/storages/folder/', params=params)
        if not response.status_code == 200:
            msg: str = f"Error {response.status_code}: Unable to establish communication with the server."
            logger.error(msg)
            raise requests.RequestException(msg)
        count = response.json().get('count')
        results: List[Optional[Dict]] = response.json().get('results')
        assert isinstance(count, int)
        if count != 0 and results:
            return results[0].get('id')
    except Exception as error:
        logger.error(f"Error: {error}")
    return None


def find_parent_folder(path: Union[str, Path], email: str, **kwargs) -> Optional[Tuple[Path, str]]:
    is_src_path: bool = kwargs.get('is_src_path', True)
    path: Path = validate_path(path)
    reference_path = Path(settings.PATH_REFERENCE).joinpath(email)
    if is_src_path:
        keyword: str = kwargs.get('keyword', "mofreitas")
        path: Path = get_path_after_keyword(path, keyword=keyword)
    parent: Optional[str] = find_folder(path.parent, is_src_path=False)
    if parent:
        return path.parent, parent
    else:
        if path.parent == reference_path:
            return None
        else:
            return find_parent_folder(path=path.parent, email=email, is_src_path=True)


def update_name(path: Path) -> bool:
    resp: Response = patch_folder(data=dict(name=path.name))
    if resp.status_code == 200:
        logger.info(f"Successfully updated the folder '{path.name}'.")
        return True
    logger.error(f"Fail to update the folder '{path.name}'.")
    return False


@validate_on_folder_created_input
def on_folder_updated(src_path: Union[str, Path], keyword: str = "mofreitas") -> bool:
    """
    Function to handle the process of updating a folder's name in a directory structure. If the parent folder or the
    target folder does not exist, it falls back to the on_folder_created function to create the necessary folders.

    Args:
        src_path (Union[str, Path]): The source path of the folder to be updated.
        keyword (str, optional): A keyword used to parse the src_path, default is "mofreitas".

    Returns:
        bool: True if the folder name is successfully updated or the necessary folders are created, False otherwise.

    Raises:
        Any exceptions raised by the underlying functions (get_path_after_keyword, get_email, find_parent_folder,
        folder_already_exists, on_folder_created, update_name) are not caught by this function.
    """
    path: Path = get_path_after_keyword(path=src_path, keyword=keyword)
    email = get_email(src_path)
    parent_path_and_id = find_parent_folder(path=path, keyword=keyword, email=email)
    # If parent does not exist or the folder itself does not exist, create the folder(s)
    if parent_path_and_id is None or not folder_already_exists(path):
        return on_folder_created(src_path=src_path)
    # Otherwise, update the name of the existing folder
    return update_name(path)


@validate_on_folder_created_input
def on_folder_created(src_path: Union[str, Path], keyword: str = "mofreitas") -> bool:
    """
    Function to handle the process of creating a folder in a directory structure.
    If the parent folder does not exist, it generates a directory with an undefined parent entity.
    The function proceeds to create the necessary child folders starting from the parent to the child.

    Args:
        src_path (Union[str, Path]): The source path of the folder to be created.
        keyword (str, optional): A keyword used to parse the src_path, default is "mofreitas".

    Returns:
        bool: True if the necessary folders are successfully created, False otherwise.

    Raises:
        Any exceptions raised by the underlying functions (get_path_after_keyword, get_email, find_parent_folder,
        create_folder, folder_already_exists) are not caught by this function.
    """
    path: Path = get_path_after_keyword(path=src_path, keyword=keyword)
    email = get_email(src_path)
    budget = get_budget_name(src_path)
    parent_path_and_id = find_parent_folder(path=path, keyword=keyword, email=email)

    if parent_path_and_id is None:
        logger.info(f"System has been unable to identify a valid parent directory. It will now endeavor to generate"
                    f" a directory with an undefined parent entity.")
        name = path.parts[path.parts.index(email) + 1]
        resp: Response = create_folder(name=name, budget_id=budget, parent=None, email=email)
        if resp.status_code == 201:
            logger.info(f"Successfully created the folder '{name}'.")
            return on_folder_created(src_path, keyword)
        else:
            logger.error(f"Error encountered while attempting to create the folder '{name}'. {resp.text}")
            return False

        # Create list of paths starting from parent to child
    paths_to_create = [parent_path_and_id[0] / part for part in path.relative_to(parent_path_and_id[0]).parts]

    for current_path in paths_to_create:
        if not folder_already_exists(current_path):
            resp: Response = create_folder(name=current_path.name, budget_id=budget, email=email,
                                           parent=parent_path_and_id[1])
            if resp.status_code == 201:
                logger.info(f"Successfully created the folder '{current_path.name}'.")
                # update parent_path_and_id for the new parent
                parent_path_and_id = (current_path, resp.json().get('id'))
            else:
                logger.error(
                    f"Error encountered while attempting to create the folder '{current_path.name}'. {resp.text}")
                return False

    return True
