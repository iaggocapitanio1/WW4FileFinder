import json

from client import oauth
from typing import Union, Optional, List, Dict
from pathlib import Path
import logging.config
import settings
from utilities.funtions import get_path_after_keyword, validate_path, get_email, get_budget_name
import requests
from requests import Request, Response

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
    return post(relative_url='/storages/folder/create_folder_with_email/', payload=payload)


def patch_folder(data: dict, **kwargs):
    payload = json.dumps(data)
    return patch(relative_url='/storages/folder/create_folder_with_email/', payload=payload)


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


def find_folder(path: Union[str, Path], **kwargs) -> List[Optional[str]]:
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
        results: List[Optional[Dict]] = response.json().grt('results')
        assert isinstance(count, int)
        if count != 0:
            return [obj.get('id') for obj in results]
    except Exception as error:
        logger.error(f"Error: {error}")
    return []


def find_parent_folder(path: Union[str, Path], **kwargs) -> Optional[Path]:
    is_src_path: bool = kwargs.get('is_src_path', True)
    keyword: str = kwargs.get('keyword', "mofreitas")
    path: Path = validate_path(path)
    if is_src_path:
        path: Path = get_path_after_keyword(path, keyword=keyword)
    parent_path = path.parent
    folders = find_folder(path, is_src_path=False)
    if folders:
        return path.parent
    else:
        if parent_path == path:
            return None
        else:
            return find_parent_folder(path=parent_path)


def process_folder(src_path: Union[str, Path], keyword: str = "mofreitas"):
    path: Path = get_path_after_keyword(path=src_path, keyword=keyword)
    valid_parent_folder_path = find_parent_folder(path=path, keyword=keyword)
    email = get_email(src_path)
    budget = get_budget_name(src_path)

    if valid_parent_folder_path == path.parent:
        if folder_already_exists(path, is_src_path=False):
            response: Response = patch_folder(data=dict(name=path.name))
            if response.status_code == 200:
                logger.info(f"Successfully updated the folder '{path.name}'.")

        else:
            parent_folder: List[Optional[str]] = find_folder(path=path, is_src_path=False)
            if parent_folder:
                response: Response = create_folder(name=path.name, budget_id=budget, email=email)
                if response.status_code == 201:
                    logger.info(f"Successfully created the folder '{path.name}'.")
                else:
                    logger.error(f"Error encountered while attempting to create the folder '{path.name}'.")
            else:
                logger.error(f"Error encountered while attempting to find the parent folder '{path.parent.name}'.")

    # If the parent folder is not found, create it
    if parent_folder is None:
        # Create the parent folder using the root user as owner and budget 'None'
        parent_folder = Folder.objects.create(folder_name=path.parts[0], user=User.objects.get(email='root'),
                                              budget=None)

    # Get a list of existing folders in the path
    existing_folders = find_folder(path=path, keyword=keyword)

    # Iterate through the path and create any missing folders
    for i in range(len(path.parts)):
        folder_path = Path(*path.parts[:i + 1])
        if folder_path not in existing_folders:
            # Create the folder
            folder_name = folder_path.parts[-1]
            budget = parent_folder.budget  # inherit budget from parent folder
            folder = Folder.objects.create(folder_name=folder_name, parent_folder=parent_folder,
                                           user=parent_folder.user, budget=budget)

            # Add the new folder to the list of existing folders
            existing_folders.append(folder_path)

        # Update the parent folder for the next iteration
        parent_folder = Folder.objects.get(path=str(folder_path))

    return str(path)

# def get_file_id(owner_email: str, project_id: str, file_name: Union[str, Path], ) -> Optional[str]:
#     logger.debug(f"received data: \n owner email: {owner_email}\n project_id: {project_id}\n category: {category}")
#     url = settings.URL + f"/storages/{category}/"
#     response = requests.request('GET', url, params=dict(project=project_id, owner__email=owner_email,
#                                                         filename=file_name), auth=oauth)
#     if response.status_code == 400:
#         logger.error(f"received the response: {response.status_code}")
#         logger.error(f"received the response: {response.json()}")
#     elif response.status_code == 200:
#         logger.debug(f"received the response: {response.status_code}")
#         logger.debug(f"received the response: {response.json()}")
#         if response.json().get('results'):
#             return response.json().get('results')[0].get('id')
#     logger.debug(f"received the response: {response.status_code}")
#     logger.debug(f"received the response: {response.json()}")
