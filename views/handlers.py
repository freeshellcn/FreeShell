#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @Author  : zhangyunjie

from PySide6.QtCore import QObject, Slot,Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui  import QFontDatabase
from models.sqlite_db import SQLiteDB
class Handlers(QObject):
    receive_data = Signal(str)
    fonts_ready = Signal(list)
    save_base_data_result = Signal(str)
    def __init__(self):
        super().__init__()
        self.view = QWebEngineView()
        self.page = self.view.page()

    @Slot()
    def load_data(self):
        db = SQLiteDB()
        data=db.query_base_data("index_page")
        self.receive_data.emit(f"{data}")

    @Slot(str)
    def save_base_data(self,data):
        db = SQLiteDB()
        save_result = db.update_base_data("index_page", data)
        self.save_base_data_result.emit(f"{save_result}")

    @Slot()
    def load_fonts(self):
        db = QFontDatabase()
        families = db.families()  # 获取所有字体族名称
        self.fonts_ready.emit(families)
