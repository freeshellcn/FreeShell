#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from PySide6.QtCore import QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from views.ssh_manager import SSHManager
from utils.copy_util import ClipboardBridge
from utils.icon_util import resource_path
from utils.xterm_config import XtermConfig
class TerminalTab(QWidget):
    def __init__(self, connect_info):
        super().__init__()
        self.connect_info = connect_info
        self.layout = QVBoxLayout(self)
        self.view = QWebEngineView()
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.manager = SSHManager(self.connect_info)
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.manager)
        self.clipboard = ClipboardBridge()
        self.channel.registerObject("clipboard", self.clipboard)
        self.view.page().setWebChannel(self.channel)
        self.xtermConfig = XtermConfig()
        self.channel.registerObject("xtermConfig", self.xtermConfig)
        self.view.page().setWebChannel(self.channel)
        # self.html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/xterm/xterm.html"))
        self.view.load(QUrl.fromLocalFile(resource_path("resources/xterm/xterm.html")))
        self.view.loadFinished.connect(self.load_view)

    def load_view(self):
        self.layout.addWidget(self.view)
        self.view.setFocus()

    # 监听窗口或容器变化，自动 fit()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view.page().runJavaScript("fitAddon.fit() ")

    def write_data(self,text):
        """通过按钮输入内容,保证窗口获得光标"""
        self.manager.send_ssh(text)
        self.view.setFocus()
        self.view.page().runJavaScript(" reset_focus()")

    def get_sftp_client(self):
        """获取SFTP连接"""
        return self.manager.get_sftp_client()

    def get_node_name(self):
        return self.connect_info["NodeName"]


