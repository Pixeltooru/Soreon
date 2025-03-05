import sys
import webbrowser
import configparser
import uuid
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                            QListWidgetItem, QProgressDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QIcon
from launcher_ui import LauncherUI
from minecraft_manager import MinecraftManager
from database import Database
from mod_manager import ModManager
from auth import AuthManager

DEBUG_MODE = "--debug_pix" in sys.argv

def debug_print(message):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

class InstallThread(QThread):
    progress_updated = pyqtSignal(int)
    message_updated = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, mc_manager, version, version_type):
        super().__init__()
        self.mc_manager = mc_manager
        self.version = version
        self.version_type = version_type

    def run(self):
        try:
            self.message_updated.emit("Начало установки...")
            self.mc_manager.install_version(
                self.version,
                self.version_type,
                lambda p: self.progress_updated.emit(p),
                lambda m: self.message_updated.emit(m)
            )
            self.finished.emit()
        except Exception as e:
            debug_print(f"Ошибка: {str(e)}")
            self.message_updated.emit(f"Ошибка: {str(e)}")

class SoreonLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.minecraft_process = None
        self.config = self.load_config()
        self.db = Database(self.config)
        self.auth = AuthManager(self.config)
        self.mc_manager = MinecraftManager(self.db, self.config)
        self.mod_manager = ModManager(self.config)
        self.init_ui()
        self.load_content()
        self.check_auth()
        self.auth.signals.authenticated.connect(self.check_auth)

    def load_config(self):
        config = configparser.ConfigParser()
        with open('config.ini', 'r', encoding='utf-8') as f:
            config.read_file(f)
        return config

    def init_ui(self):
        self.ui = LauncherUI()
        self.ui.setup_ui(self)
        self.setup_mods_list()
        self.apply_styles()
        self.connect_signals()
        self.setWindowIcon(QIcon('assets/icon.png'))
        self.setWindowTitle("Soreon Launcher")

    def setup_mods_list(self):
        try:
            mods = self.mod_manager.get_featured_mods()
            self.ui.mods_list.clear()
            for mod in mods[:50]:
                item = QListWidgetItem(mod['name'])
                item.setData(Qt.UserRole, mod)
                self.ui.mods_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить моды")

    def apply_styles(self):
        try:
            with open("assets/styles.qss", "r", encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            debug_print("Файл стилей не найден")

    def connect_signals(self):
        self.ui.login_button.clicked.connect(self.open_login)
        self.ui.logout_button.clicked.connect(self.logout)
        self.ui.install_button.clicked.connect(self.install_minecraft)
        self.ui.mods_button.clicked.connect(lambda: self.ui.mods_panel.setVisible(not self.ui.mods_panel.isVisible()))
        self.ui.play_button.clicked.connect(self.launch_game)
        self.ui.mods_list.itemDoubleClicked.connect(self.install_mod)
        self.ui.version_type_selector.currentIndexChanged.connect(self.load_versions)
        if hasattr(self.ui, 'refresh_mods_button'):
            self.ui.refresh_mods_button.clicked.connect(self.setup_mods_list)

    def check_auth(self):
        if self.auth.is_authenticated():
            self.ui.username_label.setText(self.auth.get_username())
            self.ui.login_button.hide()
            self.ui.logout_button.show()
        else:
            self.ui.logout_button.hide()

    def load_content(self):
        self.load_versions()

    def load_versions(self):
        version_type = self.ui.version_type_selector.currentText().lower()
        versions = self.mc_manager.get_available_versions(version_type)
        self.ui.version_selector.clear()
        self.ui.version_selector.addItems(versions)

    def open_login(self):
        self.auth.authenticate()

    def logout(self):
        self.auth.logout()
        self.check_auth()

    def install_minecraft(self):
        version = self.ui.version_selector.currentText()
        version_type = self.ui.version_type_selector.currentText().lower()
        if not version:
            QMessageBox.warning(self, "Ошибка", "Выберите версию")
            return

        self.install_thread = InstallThread(self.mc_manager, version, version_type)
        self.install_thread.progress_updated.connect(self.ui.progress_bar.setValue)
        self.install_thread.message_updated.connect(lambda m: self.ui.progress_bar.setFormat(f"{m} %p%"))
        self.install_thread.finished.connect(lambda: self.ui.progress_bar.setVisible(False))
        self.ui.progress_bar.setVisible(True)
        self.install_thread.start()

    def install_mod(self, item):
        mod = item.data(Qt.UserRole)
        try:
            self.mod_manager.download_mod(mod['id'], mod['downloadUrl'])
            QMessageBox.information(self, "Успех", f"Мод {mod['name']} установлен!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

    def launch_game(self):
        version = self.ui.version_selector.currentText()
        if not version:
            QMessageBox.warning(self, "Ошибка", "Выберите версию")
            return

        if not self.auth.is_authenticated():
            QMessageBox.warning(self, "Ошибка", "Требуется авторизация")
            return

        try:
            self.minecraft_process = QProcess()
            self.minecraft_process.finished.connect(self.on_game_exit)
            self.mc_manager.launch(version, self.minecraft_process, {
                'username': self.auth.get_username(),
                'uuid': self.auth.get_uuid(),
                'accessToken': self.auth.get_access_token()
            })
            self.hide()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def on_game_exit(self):
        self.show()
        self.minecraft_process = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = SoreonLauncher()
    launcher.show()
    sys.exit(app.exec_())