#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from PySide6.QtWidgets import  QApplication
from views.main_window import MainWindow
from utils.config_util import FreeShellConfig
from views.license_dialog import LicenseDialog
class MainController:

    def __init__(self):
        self.view = MainWindow()
        self.show_center() # 居中显示
        self.view.showMaximized() # 最大化
        self.license = LicenseDialog()
        self.check_licence()

    def show_center(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.view.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.view.move(window_geometry.topLeft())

    def check_licence(self):
        """用户必须同意协议才能使用"""
        licence_read_click = FreeShellConfig.get("licence_read_click")
        if not licence_read_click:
            self.license.exec()