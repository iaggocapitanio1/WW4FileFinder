from utilities.query import on_folder_updated
from client import oauth
import requests
import os
path = "mofreitas/clientes/bruno.barros@nka.pt/Chanut/project/ALPHACAM"
dest_path = "mofreitas/clientes/bruno.barros@nka.pt/Chanut/project/ALPHACAM2"
#
# relative_url = '/storages/folder/'
#
# pk = "1"
#
#
on_folder_updated(src_path=path, dest_path=dest_path)
# url = f"http://127.0.0.1:8000/api/v1/storages/folder/folder_LxbGjDeDd4eaK9PX/"
# res = requests.get(url, auth=oauth)
# print(res)
