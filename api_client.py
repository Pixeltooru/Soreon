import requests
import json

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        
    def get_user_profile(self) -> dict:
        response = self.session.get(f"{self.base_url}profile")
        return response.json()
    
    def search_mods(self, query: str) -> list:
        params = {'q': query}
        response = self.session.get(f"{self.base_url}search/mods", params=params)
        return response.json()['results']
    
    def sync_resources(self, resources: list):
        response = self.session.post(f"{self.base_url}sync", json=resources)
        return response.status_code == 200