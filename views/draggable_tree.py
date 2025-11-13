#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @Author  : zhangyunjie

from PySide6.QtWidgets import (QTreeWidget,QAbstractItemView)
from PySide6.QtCore import Qt,QTimer
from PySide6.QtGui import QFont
from models.sqlite_db import SQLiteDB


def update_move(pk_id, parent_id, seq):
    if not pk_id:
        return
    db=SQLiteDB()
    db.update_move(pk_id,parent_id,seq)

class DraggableTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        font = QFont()
        font.setPointSize(12)  # 设置字体大小
        self.setFont(font)
        # 存储被拖动的项目
        self.draggedItem = None
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove) # 内部移动模式

    def startDrag(self, supported_actions):
        # 记录被拖动的项目
        self.draggedItem = self.currentItem()
        super().startDrag(supported_actions)

    def dropEvent(self, event):
        # 执行默认的拖放操作
        super().dropEvent(event)
        # 延迟获取节点信息，确保拖放操作已完成
        if self.draggedItem:
            QTimer.singleShot(50, self.printSiblingsAfterDrop)

    def getNodeId(self, item):
        """获取节点的ID"""
        return item.data(0, Qt.ItemDataRole.UserRole) if item else None

    def printSiblingsAfterDrop(self):
        if not self.draggedItem:
            return
        # 获取移动后项目的新父节点
        new_parent = self.draggedItem.parent() or self.invisibleRootItem()
        # 获取父节点ID (顶级节点使用特殊标识)
        parent_id = self.getNodeId(new_parent) if new_parent != self.invisibleRootItem() else None
        if parent_id:
            parent_id=parent_id["PkId"]
        for i in range(new_parent.childCount()):
            sibling = new_parent.child(i)
            sibling_id = self.getNodeId(sibling)
            update_move(f"{sibling_id['PkId']}", parent_id,  f"{i + 1}")





