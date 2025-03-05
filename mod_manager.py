import os
import requests
from typing import List, Dict

class ModManager:
    def __init__(self, config):
        self.config = config
        self.mod_dir = os.path.expanduser(config['Mods']['mods_dir'])
        self.api_key = config['Mods']['curseforge_api_key']

    def get_featured_mods(self) -> List[Dict]:
        url = "https://api.curseforge.com/v1/mods/search"
        params = {
            'gameId': 432,
            'sort': 6,
            'pageSize': 50
        }
        headers = {'x-api-key': self.api_key}
        response = requests.get(url, params=params, headers=headers)
        return response.json()['data']

    def download_mod(self, mod_id: int, file_url: str):
        file_path = os.path.join(self.mod_dir, f"{mod_id}.jar")
        response = requests.get(file_url, stream=True)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)