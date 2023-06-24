import json
import logging.config
from pathlib import Path
from typing import Union, Optional, List, Dict
from urllib import parse
import mimetypes
import requests
from requests import Response

import settings
from utilities.folders import find_folder, on_folder_created
from utilities.funtions import get_path_after_keyword, validate_path
from utilities.http_requests import post, delete, get, session, ends_with_slash, normalize_relative_url

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)


def create_file(file_path: Path, keyword: str = "mofreitas" ) -> bool:
    file_path = validate_path(file_path)
    # file_path = get_path_after_keyword(file_path, keyword)
    try:
        folder_pk = find_folder(file_path.parent)
        if not folder_pk:
            logger.error(f"Folder not found! pk = '{folder_pk}'")
            # add this line to create the folder, syncthing issue
            on_folder_created(file_path.parent)
            return create_file(file_path)
        if not file_path.is_file():
            logging.error(f"The path {file_path} does not point to a file.")
            return False

        with file_path.open('rb') as file:
            mime_type, _ = mimetypes.guess_type(file_path.name)
            files = {'file': (file_path.name, file, mime_type if mime_type else 'application/octet-stream')}
            payload = {"folder": folder_pk}
            res = post(relative_url='/storages/file/', data=payload, files=files)
            if res.status_code == 201:
                logging.info(f"File {file_path.name} was successfully uploaded to the folder with ID {folder_pk}.")
                return True
            else:
                logging.error(
                    f"Failed to upload file {file_path.name} to the folder with ID {folder_pk}. "
                    f"Server responded with status code: {res.status_code}")
                logger.error(res.text)
                return False
    except Exception as error:
        logger.error(error)
        return False


def patch_file(src_path: Path, dest_path: Path, **kwargs) -> bool:
    if not dest_path.is_file():
        logger.error(f"Can not find a folder! Uses instead {find_folder.__name__}´.")
        return False
    try:
        pk = find_file(file_path=src_path)
        if not pk:
            logger.error(f"File not found! pk = '{pk}'")
            return False
        payload = json.dumps(dict(file_name=dest_path.name))
        headers = {'Content-Type': 'application/json'}
        url = parse.urljoin(ends_with_slash(settings.URL),
                            normalize_relative_url(f'/storages/file/{pk}/update_file_name/'))
        res = session.patch(url=url, data=payload, headers=headers)
        if res.status_code == 200:
            logger.info(f"Successfully updated the filename for file with pk: {pk}")
            return True
        else:
            logger.error(f"Error: Unable to update the filename for file with pk: {pk}. Status code: {res.status_code}")
            return False
    except Exception as error:
        logger.error(error)
        return False


def delete_file(path: Path) -> bool:
    file_pk = find_file(path)
    if not file_pk:
        logger.error(f"Unable to find file '{path.name}' with pk '{file_pk}'."
                     f" Deletion process cannot be initiated.")
        return False
    res = delete(relative_url='/storages/file/', pk=file_pk)
    if res.status_code == 204:
        logger.info(f"File '{path.name}' successfully deleted. Status Code '{res.status_code}'")
        return True
    else:
        logger.error(f"Deletion failed for file '{path}'.  Status Code '{res.status_code}'")
        return False


def find_file(file_path: Union[str, Path], **kwargs) -> Optional[str]:
    """
    This function attempts to locate a specific file based on the provided file path.

    Args:
    file_path (Union[str, Path]): The original path where the file is to be found.
    **kwargs: Arbitrary keyword arguments.
    - is_src_path (bool, optional): If True, the function will get the path after a specified keyword. Default is True.
    - keyword (str, optional): The keyword used to trim the original path if is_src_path is True. Default is
    "mofreitas".

    Returns: Optional[str]: If a file is found, the function returns the file id. If no file is found or an error
    occurs, None is returned.

    Raises:
    requests.RequestException: If the status code of the server's response is not 200, an exception is raised.

    Notes:
    This function operates in conjunction with the '/storages/file/' endpoint of the server and is part of a larger
    script that provides functionality for manipulating files within a storage system.
    """
    file_path = validate_path(file_path)
    keyword: str = kwargs.get('keyword', "mofreitas")
    file_path = get_path_after_keyword(file_path, keyword)
    folder_id = find_folder(file_path.parent, **kwargs)
    if folder_id is None:
        logger.error(f"No folder found for path {file_path.parent}")
        return None

    try:
        params: dict = dict(folder=folder_id, file_name=file_path.stem)
        response: Response = get(relative_url='/storages/file/', params=params)
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


def on_file_created(src_path: Union[str, Path], keyword: str = 'mofreitas') -> bool:
    """
       Function to handle the process of creating a file in a directory structure.
       The function assumes that the parent folder already exists.

       Args:
           src_path (Union[str, Path]): The source path of the file to be created.
           keyword (str, optional): A keyword used to parse the src_path, default is "mofreitas".

       Returns:
           bool: True if the file is successfully created, False otherwise.

       Raises:
           Any exceptions raised by the underlying functions (get_path_after_keyword, get_email, find_folder,
           create_file, file_already_exists) are not caught by this function.
       """
    return create_file(file_path=src_path)


def on_file_updated(src_path: Union[str, Path], dest_path: Union[str, Path], keyword: str = "mofreitas") -> bool:
    src_path = validate_path(src_path)
    dest_path = validate_path(dest_path)
    return patch_file(src_path=src_path, dest_path=dest_path)


def on_file_deleted(src_path: Union[str, Path]) -> bool:
    src_path = validate_path(src_path)
    return delete_file(path=src_path)
