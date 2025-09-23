from dataclasses import dataclass

from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Slot, Signal,
    QCoreApplication
)


@dataclass
class TransferItem:
    """文件传输内容"""
    trans_type: str
    file_type:str
    trans_time: str
    local_file: str
    remote_file:str
    file_size: int
    trans_size: int
    trans_status: str
    file_base_path: str



class TransferAbstractTableModel(QAbstractTableModel):
    """文件传入表头"""
    HEADERS = ["传输类型","文件类型","开始时间", "本地", "远程", "文件大小", "传输大小", "百分比", "状态","序号"]
    add_file_transfer_list_finished = Signal() # 添加到传输列表中
    file_transfer_finished = Signal() # 文件传输完成

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: list[TransferItem] = []
        self.trans_file_list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.items)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        item = self.items[index.row()]
        col = index.column()

        # Text 显示
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return item.trans_type
            if col == 1:
                return item.file_type
            if col == 2:
                return item.trans_time
            if col == 3:
                return item.local_file
            if col == 4:
                return item.remote_file
            if col == 5:
                return item.file_size
            if col == 6:
                return item.trans_size
            if col == 7:
                p = int(item.trans_size * 100 / item.file_size) if item.file_size else 0
                if not item.file_size and item.trans_status=='已完成':
                    p=100
                return f"{p}%"
            if col == 8:
                return item.trans_status
            if col == 9:
                return  int(index.row() + 1)

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def flags(self, index: QModelIndex):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable # type: ignore

    def add_item(self, item: TransferItem):
        """添加文件到列表中"""
        row_num = len(self.items)
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.items.append(item)
        self.trans_file_list.append(row_num)
        self.endInsertRows()
        QCoreApplication.processEvents() #重绘页面
        self.add_file_transfer_list_finished.emit()

    @Slot(int, int, str)
    def update_item(self, row: int, trans_size: int, total_size: int,error=-1):
        """文件传输进度,传输状态"""
        item = self.items[row]
        item.trans_size = trans_size
        trans_status = '已完成' if trans_size == total_size else '传输中'
        if error==1:
            trans_status='没有权限'
        elif error==2:
            trans_status='文件不存在'
        elif error==3:
            trans_status='上传失败'
        elif error == 4:
            trans_status = '无法创建上级目录'
        elif error == 5:
            trans_status = '用户取消'
        elif error == 6:
            trans_status = '跳过文件'
        item.trans_status = trans_status
        item.file_size=total_size
        top = self.index(row, 0)
        bottom = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(top, bottom,[Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.UserRole])
        QCoreApplication.processEvents() # 重绘页面
        if trans_size >= total_size:
            self.file_transfer_finished.emit() # 传输完成

class TransferSortFilterProxyModel(QSortFilterProxyModel):
    """传输文件列表排序"""
    # TODO 功能待完善
    # 状态排序权重：传输中=0，等待中=1，已完成=2
    order = {"传输中": 0, "等待中": 1, "已完成": 2}
    def lessThan(self, left, right):
        # 只拦截状态列
        # if left.column() == 5:
        #     l, r = left.data(), right.data()
        #     return self.order[l] < self.order[r]
        # 其余列回退到默认
        return super().lessThan(left, right)