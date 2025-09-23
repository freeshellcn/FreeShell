#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys

from PySide6.QtCore import QTranslator, QLibraryInfo, QLocale
from PySide6.QtWidgets import QApplication
from controllers.main_controller import MainController
from controllers.config_controller import db_init

if sys.platform.startswith("win"):
    try:
        from ctypes import windll
        myappid = "cn.freeshell.app"
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

def main():
    db_init()
    app = QApplication(sys.argv)

    # 加载 Qt 自带的中文翻译,是否类的按钮,翻译为中文
    translator = QTranslator()
    qt_trans_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    translator.load(QLocale(QLocale.Language.Chinese, QLocale.Country.China), "qtbase", "_", qt_trans_path)
    app.installTranslator(translator)

    controller = MainController()
    controller.view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
