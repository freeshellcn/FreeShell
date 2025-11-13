#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @Author  : zhangyunjie

import os
from PySide6.QtCore import QUrl
from PySide6.QtWebChannel import QWebChannel
from views.QWebEngineViewOverride import QWebEngineViewOverride
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout
)
from views.handlers import Handlers
from utils.icon_util import resource_path
class IndexTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.view = QWebEngineViewOverride()
        self.handler = Handlers()
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.handler)
        self.view.page().setWebChannel(self.channel)
        #self.html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/xterm/index.html"))
        self.view.load(QUrl.fromLocalFile(resource_path("resources/xterm/index.html")))
        self.layout.addWidget(self.view)

