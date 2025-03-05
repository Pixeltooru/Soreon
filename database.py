import sqlite3
import json
import configparser
from typing import List, Dict, Optional
from PyQt5.QtCore import QMutex

class Database:
    _instance = None
    _mutex = QMutex()

    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.init_db(config)
        return cls._instance

    def init_db(self, config=None):
        try:
            if config and config.has_section('Database'):
                db_path = config.get('Database', 'path')
            else:
                db_path = 'soreon.db'
        except (configparser.NoSectionError, configparser.NoOptionError):
            db_path = 'soreon.db'

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_tables()

    def init_tables(self):
        cursor = self.conn.cursor()
        
        # Создание таблицы версий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY,
                version TEXT UNIQUE,
                type TEXT,
                path TEXT,
                main_class TEXT,
                libraries TEXT
            )
        """)
        
        # Проверка и добавление отсутствующих колонок
        cursor.execute("PRAGMA table_info(versions)")
        columns = {column[1] for column in cursor.fetchall()}
        
        if 'main_class' not in columns:
            cursor.execute("ALTER TABLE versions ADD COLUMN main_class TEXT")
        if 'libraries' not in columns:
            cursor.execute("ALTER TABLE versions ADD COLUMN libraries TEXT")

        # Создание таблицы модов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mods (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                version TEXT,
                file_path TEXT,
                mod_id TEXT
            )
        """)
        
        self.conn.commit()

    def save_version(self, version: str, version_type: str, path: str, main_class: str, libraries: list):
        self._mutex.lock()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO versions 
                (version, type, path, main_class, libraries)
                VALUES (?, ?, ?, ?, ?)
            """, (version, version_type, path, main_class, json.dumps(libraries)))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            self._mutex.unlock()

    def get_version(self, version: str) -> Optional[Dict]:
        self._mutex.lock()
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT version, type, path, main_class, libraries 
                FROM versions WHERE version = ?
            ''', (version,))
            row = cursor.fetchone()
            if row:
                return {
                    "version": row[0],
                    "type": row[1],
                    "path": row[2],
                    "main_class": row[3],
                    "libraries": json.loads(row[4]) if row[4] else []
                }
            return None
        finally:
            self._mutex.unlock()

    def save_mod(self, mod: Dict):
        self._mutex.lock()
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO mods (name, version, file_path)
                VALUES (?, ?, ?)
            ''', (mod['name'], mod['version'], mod['file_path']))
            self.conn.commit()
        finally:
            self._mutex.unlock()

    def get_mods(self) -> List[Dict]:
        self._mutex.lock()
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM mods')
            return [{
                "id": row[0],
                "name": row[1],
                "version": row[2],
                "file_path": row[3]
            } for row in cursor.fetchall()]
        finally:
            self._mutex.unlock()