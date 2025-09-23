#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @Author  : zhangyunjie

from PySide6.QtWidgets import (QTreeWidget,QAbstractItemView)
from PySide6.QtCore import Qt
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
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        # 拖拽开始：记录原始位置
        self._dragged_info = []
        self.itemPressed.connect(self._on_item_pressed)
        font = QFont()
        font.setPointSize(12)  # 设置字体大小
        self.setFont(font)

    def _on_item_pressed(self, item, col):
        """
        当用户按下鼠标准备拖拽时，缓存当前选中的所有节点
        及其原始 parent/id/row。
        """
        self._dragged_info = []
        for it in self.selectedItems():
            parent = it.parent()
            parent_id = parent.data(0, Qt.ItemDataRole.UserRole) if parent else None
            row = (parent.indexOfChild(it)
                   if parent else self.indexOfTopLevelItem(it))
            self._dragged_info.append({
                "item": it,
                "orig_parent_id": parent_id,
                "orig_row": row,
                "id": it.data(0, Qt.ItemDataRole.UserRole)
            })

    def dragMoveEvent(self, event):
        pt     = event.position().toPoint()
        target = self.itemAt(pt)
        posf   = self.dropIndicatorPosition()
        if posf == QAbstractItemView.DropIndicatorPosition.OnItem and target:
            data = target.data(0, Qt.ItemDataRole.UserRole)
            if data and data['NodeType'] == 'item':
                event.ignore()
                return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        pt = event.position().toPoint()
        target = self.itemAt(pt)
        posf = self.dropIndicatorPosition()
        if posf == QAbstractItemView.DropIndicatorPosition.OnItem and target:
            data = target.data(0, Qt.ItemDataRole.UserRole)
            if data and data['NodeType'] == 'item':
                event.ignore()
                return
        super().dropEvent(event)
        for info in self._dragged_info:
            it = info["item"]

            # 找新 parent、new row
            new_parent = it.parent()
            new_parent_id = (new_parent.data(0, Qt.ItemDataRole.UserRole)
                             if new_parent else None)
            new_row = (new_parent.indexOfChild(it)
                       if new_parent else self.indexOfTopLevelItem(it))

            # 如果真正发生移动，就打印局部更新
            # if (info["orig_parent_id"] != new_parent_id or info["orig_row"] != new_row):
            #     print(f"节点 {info['id']} 移动："
            #           f"从父 {info['orig_parent_id']} 的第 {info['orig_row']} 行 \n"
            #           f"→ 父 {new_parent_id} 的第 {new_row} 行")
            if (info["orig_parent_id"] != new_parent_id or info["orig_row"] != new_row):
                pk_id=info['id']['PkId']
                parent_id=None
                if new_parent_id:
                    parent_id = new_parent_id['PkId']
                seq=new_row
                update_move(pk_id, parent_id, seq)
            # 清空缓存，下次拖拽重新记录
        self._dragged_info = []



