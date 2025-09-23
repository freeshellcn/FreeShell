import posixpath
import posixpath
import stat
import time
from pathlib import Path

from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
)
from PySide6.QtWidgets import (
    QApplication, QStyle
)

from utils.icon_util import get_icon
from utils.file_util import format_file_size


class ServerAbstractTableModel(QAbstractTableModel):
    headers = ["文件名", "文件大小", "文件类型", "修改时间", "权限", "所有者", "排序", "文件Size"]

    def __init__(self, sftp, parent=None):
        super().__init__(parent)
        self.sftp = sftp
        self.server_entries = []  # 每项：dict{name,size,permissions,owner,group,mtime,mtime_ts,is_dir}
        self._cwd = "/"

    def rowCount(self, parent=QModelIndex()):
        return len(self.server_entries) if not parent.isValid() else 0

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        entry = self.server_entries[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            if entry["file_type"] == "软链接":
                if entry['is_dir']:
                    return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirLinkIcon)
                else:
                    return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon)
            else:
                if entry["file_type"] == "文件夹":
                    return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
                elif entry["file_type"] == "文件不存在":
                    return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
                else:
                    suffix = Path(entry["name"]).suffix.lower()
                    if not suffix:
                        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
                    icon_data = get_icon(suffix)
                    if icon_data:
                        return icon_data
                    else:
                        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        # 对齐
        if role == Qt.ItemDataRole.TextAlignmentRole and col == 1:
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        if role == Qt.ItemDataRole.TextAlignmentRole and col in (2, 3, 4, 5):
            return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        # 显示文本
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return entry["name"]
            if col == 1:
                return entry["file_size_show"]
            if col == 2:
                return entry["file_type"]
            if col == 3:
                return entry["mtime"]
            if col == 4:
                return entry["permissions"]
            if col == 5:
                return entry["owner"]
            if col == 6:
                return entry["sort_data"]
            if col == 7:
                return str(entry["size"])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled  # type: ignore

    def get_owner(self, longname):
        result = ' '.join(longname.split()).split(" ")
        return f"{result[2]}"

    def get_file_type(self, perms):
        file_type = perms[:1]
        if file_type == "-":
            return "文件"
        elif file_type == "d":
            return "文件夹"
        elif file_type == "l":
            return "软链接"
        elif file_type == "c":
            return "串行设备"
        elif file_type == "b":
            return "磁盘设备"
        elif file_type == "s":
            return "套接字"
        elif file_type == "p":
            return "管道文件"
        else:
            return "未知类型"

    def refresh(self, path: str):
        """切换目录并读取属性，刷新表格"""
        try:
            self.beginResetModel()
            self.server_entries.clear()
            raw = self.sftp.listdir_attr(path)
            for f in raw:
                perms = stat.filemode(f.st_mode)
                file_type = self.get_file_type(perms)
                fullpath = posixpath.join(path, f.filename)
                is_link = stat.S_ISLNK(f.st_mode)
                try:
                    is_dir = stat.S_ISDIR(self.sftp.stat(fullpath).st_mode)
                except OSError:
                    is_dir = False
                    file_type = '文件不存在'
                target = None
                if is_link:
                    try:
                        target = self.sftp.readlink(fullpath)
                    except:
                        target = "unresolved"

                mtime_ts = f.st_mtime
                mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime_ts))
                sort_data = f"{str(1 if is_dir else 2)}{f.filename}"
                file_size = ''
                if not is_dir:
                    file_size = format_file_size(f.st_size)
                self.server_entries.append({
                    "name": f.filename,
                    "size": f.st_size,
                    "file_type": file_type,
                    "mtime": mtime_str,
                    "permissions": perms,
                    "owner": self.get_owner(f.longname),
                    "symlink_target": target,
                    "is_dir": is_dir,
                    "sort_data": sort_data,
                    "file_size_show": file_size
                })
            self._cwd = path
        except Exception as e:
            print(f"刷新目录失败: {e}")
            raise e
        finally:
            self.endResetModel()

    def cwd(self) -> str:
        return self._cwd


class ServerSortFilterProxyModel(QSortFilterProxyModel):
    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        sort_col = self.sortColumn()
        # 第一列排序 默认按照第六列排序 文件夹在前, 然后是文件
        if sort_col == 0:
            left_name = left.sibling(left.row(), 6).data(Qt.ItemDataRole.DisplayRole).lower()
            right_name = right.sibling(right.row(), 6).data(Qt.ItemDataRole.DisplayRole).lower()
            return left_name > right_name
        elif sort_col == 1:
            left_name = left.sibling(left.row(), 7).data(Qt.ItemDataRole.DisplayRole).lower()
            left_type = left.sibling(left.row(), 2).data(Qt.ItemDataRole.DisplayRole).lower()
            if not left_type or left_type == "文件夹":
                left_name=-1
            right_name = right.sibling(right.row(), 7).data(Qt.ItemDataRole.DisplayRole).lower()
            right_type = right.sibling(right.row(), 2).data(Qt.ItemDataRole.DisplayRole).lower()
            if not right_type or right_type == "文件夹":
                right_name=-1
            return int(left_name) > int(right_name)
        else:
            # 其它列 正常排序
            left_val = str(left.data(Qt.ItemDataRole.DisplayRole)).lower()
            right_val = str(right.data(Qt.ItemDataRole.DisplayRole)).lower()
            return left_val < right_val
