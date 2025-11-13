#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import webbrowser
from PySide6.QtWidgets import (QVBoxLayout,QDialog, QLabel, QMessageBox)
from PySide6.QtCore import Qt

from utils.config_util import FreeShellConfig
from views.use_third_soft import UseThirdSoftDialog


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于我们")
        self.resize(400, 200)

        label = QLabel(self)
        label.setOpenExternalLinks(False)  # 禁止自动跳转，自己处理点击
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        text = (
            "FreeShell <br><br>"
            "• 开源免费的连接Linux服务器客户端工具<br><br>"
            "• 版权所有: @freeshell.cn<br><br>"
            f"• 软件版本: {FreeShellConfig.SOFT_VERSION}<br><br>"
            "• 官网地址: <a href='freeshell'>https://www.freeshell.cn</a><br><br>"
            "• 官网地址: <a href='github'>github地址</a><br><br>"
            "• 官网地址: <a href='gitee'>gitee地址</a><br><br>"
            "• <a href='thirdsoft'>使用第三方软件</a>"
        )
        label.setText(text)

        layout = QVBoxLayout(self)
        layout.addWidget(label)

        # 连接信号
        label.linkActivated.connect(self.link_clicked)

    def link_clicked(self, link: str):
        if link == "thirdsoft":
            soft = UseThirdSoftDialog()
            soft.exec()
        elif link == "freeshell":
            webbrowser.open("https://www.freeshell.cn")
        elif link == "github":
            webbrowser.open("https://github.com/freeshellcn/FreeShell")
        elif link == "gitee":
            webbrowser.open("https://gitee.com/freeshellcn/FreeShell")

