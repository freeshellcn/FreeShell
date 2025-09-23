#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox
)

from models.sqlite_db import SQLiteDB
from utils.config_util import FreeShellConfig
from utils.icon_util import resource_path


class SettingForm(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = '全局设置'
        self.db = SQLiteDB()
        self.setWindowTitle(self.title)
        self.resize(600, 200)
        self.parent_id = None  # 隐藏父ID
        self.setWindowIcon(QIcon(resource_path("resources/image/Logo.png")))
        self.pk_id_edit = None

        # 底部保存取消按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("保存")
        self.cancel_btn = QPushButton("取消")
        self.save_btn.clicked.connect(self.on_save)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        # 布局汇总
        main_layout = QVBoxLayout()
        button_group = QGroupBox("鼠标控制")
        form_layout = QFormLayout(button_group)
        self.mouse_left = QComboBox()
        self.mouse_left.addItems(["开启", "关闭"])
        mouse_left_text = FreeShellConfig.get("mouse_left_select")
        if mouse_left_text:
            self.mouse_left.setCurrentText(mouse_left_text)
        form_layout.addRow("左击复制:", self.mouse_left)
        self.mouse_right = QComboBox()
        self.mouse_right.addItems(["开启", "关闭"])
        mouse_right_text = FreeShellConfig.get("mouse_right_paste")
        if mouse_right_text:
            self.mouse_right.setCurrentText(mouse_right_text)
        form_layout.addRow("右击粘贴:", self.mouse_right)

        main_layout.addWidget(button_group)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def on_save(self):
        FreeShellConfig.update_freeshell_config("mouse_left_select", self.mouse_left.currentText())
        FreeShellConfig.update_freeshell_config("mouse_right_paste", self.mouse_right.currentText())
        self.accept()

    def exec_show(self):
        return self.exec()
