import os
import uuid
import requests
import platform
from typing import List, Dict, Callable
from PyQt5.QtCore import QMutex, QProcess
from minecraft_launcher_lib.utils import get_minecraft_directory
from minecraft_launcher_lib.command import get_minecraft_command
from minecraft_launcher_lib.install import install_minecraft_version
from bs4 import BeautifulSoup

class MinecraftManager:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.minecraft_dir = os.path.expanduser(config['Launcher']['minecraft_dir'])
        self.natives_platform = self._get_natives_platform()
        self.ensure_directories()
        self._mutex = QMutex()

    def _get_natives_platform(self):
        system = platform.system().lower()
        return {
            'windows': 'natives-windows',
            'linux': 'natives-linux',
            'darwin': 'natives-macos'
        }.get(system, 'natives-linux')

    def ensure_directories(self):
        required_dirs = ['versions', 'mods', 'libraries', 'assets', 'natives']
        for d in required_dirs:
            os.makedirs(os.path.join(self.minecraft_dir, d), exist_ok=True)

    def get_available_versions(self, version_type: str) -> List[str]:
        try:
            if version_type == "vanilla":
                return self._get_vanilla_versions()
            elif version_type == "fabric":
                return self._get_fabric_versions()
            elif version_type == "forge":
                return self._get_forge_versions()
            return []
        except Exception as e:
            print(f"Error getting versions: {str(e)}")
            return []

    def _get_vanilla_versions(self) -> List[str]:
        response = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json")
        return [v['id'] for v in response.json()['versions'] if v['type'] == 'release']

    def _get_fabric_versions(self) -> List[str]:
        response = requests.get("https://meta.fabricmc.net/v2/versions/game")
        return [v['version'] for v in response.json()]

    def _get_forge_versions(self) -> List[str]:
        response = requests.get("https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json")
        return list(response.json()['promos'].keys())

    def install_version(self, version: str, version_type: str, progress_cb: Callable, message_cb: Callable):
        try:
            if version_type == "vanilla":
                self._install_vanilla(version, progress_cb, message_cb)
            elif version_type == "fabric":
                self.install_fabric(version, progress_cb, message_cb)
            elif version_type == "forge":
                self.install_forge(version, progress_cb, message_cb)
            else:
                raise NotImplementedError(f"Тип {version_type} не поддерживается")
        except Exception as e:
            message_cb(f"Ошибка установки: {str(e)}")
            raise

    def _install_vanilla(self, version: str, progress_cb: Callable, message_cb: Callable):
        message_cb("Установка версии...")
        install_minecraft_version(version, self.minecraft_dir, callback={
            'setStatus': message_cb,
            'setProgress': progress_cb
        })

        self.db.save_version(
            version=version,
            version_type='vanilla',
            path=os.path.join(self.minecraft_dir, 'versions', version, f"{version}.jar"),
            main_class="net.minecraft.client.main.Main",
            libraries=[]
        )

    def install_fabric(self, version: str, progress_cb: Callable, message_cb: Callable):
        try:
            message_cb("Получение Fabric Installer...")
            loader_url = f"https://meta.fabricmc.net/v2/versions/loader/{version}"
            response = requests.get(loader_url)
            if response.status_code != 200:
                raise Exception("Не удалось получить данные Fabric")
            
            fabric_data = response.json()
            installer_url = f"https://maven.fabricmc.net/{fabric_data[0]['loader']['maven']}"
            installer_path = os.path.join(self.minecraft_dir, "fabric-installer.jar")
            
            message_cb("Скачивание установщика...")
            self._download_file(installer_url, installer_path)
            
            message_cb("Установка Fabric...")
            os.system(f"java -jar {installer_path} client -dir {self.minecraft_dir} -mcversion {version}")
            
            self.db.save_version(
                version=version,
                version_type='fabric',
                path=os.path.join(self.minecraft_dir, 'versions', f"fabric-loader-{version}"),
                main_class="net.fabricmc.loader.launch.knot.KnotClient",
                libraries=[]
            )
            
            message_cb("Fabric успешно установлен!")
        except Exception as e:
            message_cb(f"Ошибка: {str(e)}")
            raise

    def install_forge(self, version: str, progress_cb: Callable, message_cb: Callable):
        try:
            message_cb("Поиск Forge Installer...")
            forge_url = f"https://files.minecraftforge.net/net/minecraftforge/forge/index_{version}.html"
            response = requests.get(forge_url)
            if response.status_code != 200:
                raise Exception("Не удалось получить данные Forge")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            installer_link = soup.find("a", {"class": "btn btn-large btn-download"})['href']
            
            message_cb("Скачивание установщика...")
            installer_path = os.path.join(self.minecraft_dir, "forge-installer.jar")
            self._download_file(installer_link, installer_path)
            
            message_cb("Установка Forge...")
            os.system(f"java -jar {installer_path} --installClient")
            
            self.db.save_version(
                version=version,
                version_type='forge',
                path=os.path.join(self.minecraft_dir, 'versions', f"forge-{version}"),
                main_class="net.minecraftforge.client.ForgeClient",
                libraries=[]
            )
            
            message_cb("Forge успешно установлен!")
        except Exception as e:
            message_cb(f"Ошибка: {str(e)}")
            raise

    def _download_file(self, url: str, path: str):
        response = requests.get(url, stream=True)
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def launch(self, version: str, process: QProcess, args: dict):
        version_data = self.db.get_version(version)
        if not version_data:
            raise Exception(f"Версия {version} не установлена")

        options = {
            'username': args['username'],
            'uuid': args['uuid'],
            'token': args['accessToken'],
            'gameDirectory': self.minecraft_dir,
            'launcherName': 'Soreon Launcher',
            'launcherVersion': '1.0.0'
        }

        command = get_minecraft_command(version_data['version'], self.minecraft_dir, options)
        process.start(command[0], command[1:])