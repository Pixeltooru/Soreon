import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QComboBox, QScrollArea,
    QStackedWidget, QSizePolicy, QProgressBar
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

class LauncherUI:
    def setup_ui(self, parent):
        parent.setFixedSize(1280, 720)
        
        # контейнер
        self.central_widget = QWidget(parent)
        parent.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # панель
        self.nav_bar = QHBoxLayout()
        self.nav_bar.setObjectName("nav_bar")
        
        # Лого
        self.logo_label = QLabel()
        self.logo_label.setObjectName("logo_label")
        self.logo_label.setAlignment(Qt.AlignCenter)
        

        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            self.logo_label.setPixmap(QPixmap(logo_path).scaled(200, 50, Qt.KeepAspectRatio))
        else:
            self.logo_label.setText("SOREON LAUNCHER")
            print(f"Warning: Logo file not found at {logo_path}")
        

        self.username_label = QLabel("Пожалуйста войдите в аккаунт")
        self.mods_button = QPushButton("Моды")
        self.login_button = QPushButton("Войти")
        self.logout_button = QPushButton("Выйти")
        

        self.nav_bar.addWidget(self.logo_label)
        self.nav_bar.addWidget(self.username_label)
        self.nav_bar.addStretch()
        self.nav_bar.addWidget(self.mods_button)
        self.nav_bar.addWidget(self.login_button)
        self.nav_bar.addWidget(self.logout_button)
        

        self.main_content = QWidget()
        self.main_content.setObjectName("main_content")
        self.content_layout = QVBoxLayout(self.main_content)
        

        self.main_stack = QStackedWidget()
        

        self.launch_panel = QWidget()
        self.setup_launch_panel() 
        

        self.mods_panel = QScrollArea()
        self.setup_mods_panel()
        
        self.main_stack.addWidget(self.launch_panel)
        self.main_stack.addWidget(self.mods_panel)
        

        self.content_layout.addWidget(self.main_stack)
        self.content_layout.addStretch()
        

        self.bottom_panel = QHBoxLayout()
        self.version_type_selector = QComboBox()
        self.version_type_selector.addItems(["Vanilla", "Fabric", "Forge", "OptiFine"])
        self.version_selector = QComboBox()
        self.install_button = QPushButton("Установить")
        self.play_button = QPushButton("Играть")
        

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.bottom_panel.addWidget(QLabel("Тип:"))
        self.bottom_panel.addWidget(self.version_type_selector)
        self.bottom_panel.addWidget(QLabel("Версия:"))
        self.bottom_panel.addWidget(self.version_selector)
        self.bottom_panel.addWidget(self.install_button)
        self.bottom_panel.addWidget(self.play_button)
        self.bottom_panel.addWidget(self.progress_bar)
        

        self.main_layout.addLayout(self.nav_bar)
        self.main_layout.addWidget(self.main_content)
        self.main_layout.addLayout(self.bottom_panel)
        

        font = QFont("Segoe UI", 10)
        parent.setFont(font)


    def setup_launch_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addStretch()
        self.launch_panel = panel

    def setup_mods_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.mods_list = QListWidget()
        self.refresh_mods_button = QPushButton("Обновить список модов")  
        layout.addWidget(self.mods_list)
        layout.addWidget(self.refresh_mods_button)
        self.mods_panel.setWidget(panel)
        self.mods_panel.setWidgetResizable(True)
        self.mods_panel.setVisible(False)

    def toggle_mods_panel(self):
        self.mods_panel.setVisible(not self.mods_panel.isVisible())