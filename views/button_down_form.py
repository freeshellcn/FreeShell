#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QFormLayout, QMessageBox, QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton, QRadioButton,
    QButtonGroup
)

from models.sqlite_db import SQLiteDB
from utils.icon_util import resource_path


class ButtonDownForm(QDialog):
    insert_button_ok = Signal(str, str, int, int, int)
    update_button_ok = Signal(str, str, int, int, int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.seq = None
        self.title = '按钮信息'
        self.db = SQLiteDB()
        self.setWindowTitle(self.title)
        self.resize(600, 200)
        self.parent_id = None  # 隐藏父ID
        self.setWindowIcon(QIcon(resource_path("resources/image/Logo.png")))
        self.pk_id_edit=None

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
        button_group = QGroupBox("按钮信息")
        self.button_name = QLineEdit()
        self.button_content = QLineEdit()
        form_layout = QFormLayout(button_group)
        form_layout.addRow("按钮名称:", self.button_name)
        form_layout.addRow("按钮内容:", self.button_content)

        self.radio_button_group = QButtonGroup(self)
        # 单选按钮
        radio_group = QGroupBox("发送字符命令")
        radio_group.setWindowTitle("")
        radio_layout = QHBoxLayout(radio_group)
        self.send1 = QRadioButton('无')
        self.send2 = QRadioButton(r'\r-发送一个回车')
        self.send3 = QRadioButton(r'\n-发送一个新行')
        self.send4 = QRadioButton(r'\t-发送一个TAB')
        self.send1.setChecked(True)
        self.radio_button_group.addButton(self.send1, 1)
        self.radio_button_group.addButton(self.send2, 2)
        self.radio_button_group.addButton(self.send3, 3)
        self.radio_button_group.addButton(self.send4, 4)

        radio_layout.addWidget(self.send1)
        radio_layout.addWidget(self.send2)
        radio_layout.addWidget(self.send3)
        radio_layout.addWidget(self.send4)
        form_layout.addRow(radio_group)

        main_layout.addWidget(button_group)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def on_save(self):
        button_id = self.radio_button_group.checkedId()
        button_name = self.button_name.text()
        if not button_name:
            QMessageBox.warning(self, "按钮名称不能为空", "按钮名称不能为空")
            return
        button_content = self.button_content.text()
        if not button_content:
            QMessageBox.warning(self, "按钮内容不能为空", "按钮内容不能为空")
            return
        if not self.seq :
            self.seq = self.db.query_button_info_max_seq()
        if not self.pk_id_edit:
            pk_id = self.db.insert_button_info(button_name, button_content, self.seq, button_id)
            self.insert_button_ok.emit(button_name, button_content, pk_id, self.seq, button_id)
        else:
            self.db.update_button_info(button_name, button_content, self.seq, button_id,self.pk_id_edit)
            self.update_button_ok.emit(button_name, button_content, self.pk_id_edit, self.seq, button_id)
        self.accept()

    def exec_show(self, title="按钮信息",button_name=None, button_content=None, pk_id=None, seq=None, button_id=None):
        self.setWindowTitle(title)
        if button_name:
            self.button_name.setText(button_name)
            self.button_content.setText(button_content)
            self.seq=seq
            target_btn = self.radio_button_group.button(button_id)  # 通过value找按钮
            if target_btn:
                target_btn.setChecked(True)  # 设置选中
            self.pk_id_edit=pk_id

        return self.exec()
