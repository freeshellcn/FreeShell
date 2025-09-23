import os
import posixpath
import threading
import time
import traceback
from pathlib import Path
from stat import S_ISDIR

from PySide6.QtCore import (
    Qt, QModelIndex, Slot, QDir, QStandardPaths, QTimer
)
from PySide6.QtGui import (
    QAction, QIcon
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTreeView, QAbstractItemView,
    QLineEdit, QPushButton, QTableView, QMenu, QMessageBox, QMainWindow, QLabel, QHeaderView
)

from utils.date_util import get_datetime
from utils.file_util import get_folder_all_file
from utils.icon_util import resource_path
from views.sftp_file_transfer import (TransferSortFilterProxyModel, TransferItem, TransferAbstractTableModel)
from views.sftp_local_explorer import LocalFileSystemModel
from views.sftp_server_explorer import (ServerAbstractTableModel, ServerSortFilterProxyModel)
from views.sftp_trans_confirm import SftpTransConfirmDialog
from utils.config_util import FreeShellConfig
class UpDownLoadWindow(QMainWindow):
    """SFTP上传下载文件"""

    def __init__(self, node_name, sftp):
        super().__init__()
        self.local_reload_btn = None
        self.local_up_btn = None
        self._combo_line_edit = None
        self.local_view = None
        self.local_model = None
        self.local_path_combobox = None
        self.trans_file_monitor_running = False
        self.local_current_path = None
        try:
            self.node_name = node_name  # 窗口名称
            self.sftp = sftp
        except Exception as e:
            QMessageBox.critical(self, "连接失败", str(e))
        self.setWindowTitle("FreeShell: " + self.node_name + "  [左边本地,右边远程服务器]")
        self.resize(1280, 600)
        self.setWindowIcon(QIcon(resource_path("resources/image/Logo.png")))
        self.trans_no_prompt=False # 是否不再提示
        self.trans_skip_overwrite=None # 跳过 覆盖 skip  overwrite
        # 主窗口中央部件
        central = QWidget()
        self.setCentralWidget(central)
        # 主水平布局，左右两侧内容相同
        main_layout = QVBoxLayout(central)
        top_lay = QHBoxLayout()
        top_lay.addLayout(self.create_local_explorer(), 4)
        top_lay.addLayout(self._create_service_explorer(), 6)
        main_layout.addLayout(top_lay, 7)
        main_layout.addLayout(self._create_file_transfer_explorer(), 3)

    def create_local_explorer(self, local_start_path=None):
        """左侧本地文件"""
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        # 本地路径
        self.local_path_combobox = QComboBox()  # 本地路径下拉框
        self.local_path_combobox.setEditable(True)
        self.local_path_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.local_path_combobox.lineEdit().setPlaceholderText("输入路径后按回车切换目录")
        if FreeShellConfig.SYSTEM_TYPE=='windows':
            # [桌面] 添加到下拉框
            desktop = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)
            self.local_path_combobox.addItem("桌面", desktop)
            # 磁盘信息添加到下拉框
            for drv in QDir.drives():
                letter = drv.absoluteFilePath()
                self.local_path_combobox.addItem(letter, letter)
        # 下拉框选中
        self.local_path_combobox.activated.connect(self.local_on_combobox_activated)
        # 输入路径，按回车键
        self._combo_line_edit: QLineEdit = self.local_path_combobox.lineEdit()
        self._combo_line_edit.returnPressed.connect(self.local_on_enter_path)
        # 上级目录按钮
        self.local_up_btn = QPushButton("上级目录")
        # 点击上级目录按钮
        self.local_up_btn.clicked.connect(self.local_go_to_parent)
        # 刷新按钮
        self.local_reload_btn = QPushButton("刷新")
        self.local_reload_btn.clicked.connect(self.local_refresh)
        hbox.addWidget(QLabel("本地路径"))
        hbox.addWidget(self.local_path_combobox, 1)  # 输入框获得布局剩余空间
        hbox.addWidget(self.local_up_btn)  # 按钮仅占它的推荐大小
        hbox.addWidget(self.local_reload_btn)
        vbox.addLayout(hbox)

        # 文件系统模型 & 视图
        self.local_model = LocalFileSystemModel()
        self.local_model.setRootPath(QDir.rootPath())
        self.local_model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)  # type: ignore
        # 文件列表
        self.local_view = QTreeView()
        self.local_view.setModel(self.local_model)
        local_header = self.local_view.header()
        local_header.setStretchLastSection(False)  # 最后一列不强制撑满，方便拖动
        local_header.setSectionsMovable(True)  # 表头列可交换位置（可选）
        local_header.setSectionsClickable(True)  # 点击可排序（和排序配合）
        # 每列设置 resize 模式
        local_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 文件名列自动撑开
        local_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # 大小列：可拖动
        local_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # 修改时间列：可拖动
        self.local_view.doubleClicked.connect(self.local_on_item_double_clicked)
        self.local_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.local_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.local_view.customContextMenuRequested.connect(self.local_show_context_menu)
        self.local_view.setSortingEnabled(True)
        self.local_model.sort(0, Qt.SortOrder.AscendingOrder)
        self.local_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.local_view.hideColumn(2) # 隐藏第3列,文件类型
        vbox.addWidget(self.local_view)
        # 初始目录
        self.local_current_path = local_start_path or QDir.homePath()
        self.local_change_directory(self.local_current_path)
        return vbox

    def local_on_combobox_activated(self, index: int):
        """ 选中下拉框地址 桌面或某个盘符"""
        data = self.local_path_combobox.itemData(index)
        self.local_change_directory(data)

    def local_change_directory(self, path: str):
        """切换目录"""
        index = self.local_model.index(path)
        if not index.isValid():
            return
        self.local_view.setRootIndex(index)
        self.local_current_path = path
        self.local_path_combobox.setCurrentText(path)

    def local_on_enter_path(self):
        """输入路径按回车 切换路径"""
        new_path = self.local_path_combobox.currentText().strip()
        if os.path.isdir(new_path):
            self.local_change_directory(new_path)
        else:
            QMessageBox.warning(
                self, "目录不存在",
                f"无法找到目录：{new_path}\n请检查路径是否正确。"
            )
            # 恢复显示
            self.local_path_combobox.setCurrentText(self.local_current_path)

    def local_refresh(self):
        """刷新本地文件"""
        path = self.local_path_combobox.currentText()
        self.local_change_directory(path)
        self.local_model.setRootPath("")  # 重置
        self.local_model.setRootPath(path)  # 再设置回来

    def local_go_to_parent(self):
        """上一层：到达盘符根时，也可弹出盘符菜单"""
        parent = os.path.dirname(self.local_current_path)
        if parent and parent != self.local_current_path and os.path.isdir(parent):
            self.local_change_directory(parent)

    def local_on_item_double_clicked(self, idx):
        """双击目录或文件， 目录进入下一层， 文件忽略"""
        path = self.local_model.filePath(idx)
        if os.path.isdir(path):
            self.local_change_directory(path)
        else:
            self.upload_init([Path(path).as_posix()])

    def local_show_context_menu(self, pos):
        """文件或文件夹右击"""
        indexes = self.local_view.selectionModel().selectedIndexes()
        selected_rows = set(index.row() for index in indexes if index.column() == 0)
        selected_indexes = [
            idx for idx in indexes if idx.column() == 0 and idx.row() in selected_rows
        ]
        if not selected_indexes:
            return
        paths = [self.local_model.filePath(idx) for idx in selected_indexes]
        menu = QMenu(self)
        upload = QAction("上传", self)
        upload.triggered.connect(lambda: self.upload_init(paths))
        menu.addAction(upload)

        local_refresh = QAction("刷新", self)
        local_refresh.triggered.connect(lambda: self.local_refresh)
        menu.addAction(local_refresh)

        menu.exec(self.local_view.viewport().mapToGlobal(pos))

    def _create_file_transfer_explorer(self):
        """文件传输进度"""
        transfer_lay = QVBoxLayout()
        # 模型 + 代理 + 视图
        self.file_transfer_model = TransferAbstractTableModel(self)
        self.file_transfer_proxy = TransferSortFilterProxyModel(self)
        self.file_transfer_proxy.setSourceModel(self.file_transfer_model)
        self.file_transfer_proxy.setDynamicSortFilter(True)
        self.file_transfer_model.add_file_transfer_list_finished.connect(self.trans_file_monitor)
        self.file_transfer_model.file_transfer_finished.connect(self.server_refresh)
        self.file_transfer_view = QTableView()
        self.file_transfer_view.setModel(self.file_transfer_proxy)
        self.file_transfer_view.verticalHeader().setVisible(False)  # 隐藏默认行号
        self.file_transfer_view.setSortingEnabled(True)  # 默认开启排序
        self.file_transfer_view.sortByColumn(9, Qt.SortOrder.DescendingOrder)

        # 延迟执行（等待视图加载完）, 直接加载宽度设置失败
        QTimer.singleShot(0, self.adjust_column_widths)
        transfer_lay.addWidget(self.file_transfer_view)
        return transfer_lay
        # 窗口改变大小,重新设置宽度

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_column_widths()
        self.adjust_column_widths2()

    # 评价分配,设置宽度
    def adjust_column_widths(self):
        total_width = self.file_transfer_view.viewport().width()
        column_count = self.file_transfer_model.columnCount()
        for col in range(column_count):
            self.file_transfer_view.setColumnWidth(col, int(total_width / column_count))

    def adjust_column_widths2(self):
        total_width = self.server_view.viewport().width()
        for col in range(6):
            self.server_view.setColumnWidth(col, int(total_width / 6))

    def _create_service_explorer(self):
        """右侧服务器文件"""
        real_path = self.sftp.normalize('.')
        # 地址栏 & 上级目录
        self.server_path_edit = QLineEdit(real_path)
        self.server_path_edit.returnPressed.connect(self.server_on_path_enter)

        self.server_up_btn = QPushButton("上级目录")
        self.server_up_btn.clicked.connect(self.server_go_up)

        # 刷新按钮
        self.server_reload_btn = QPushButton("刷新")
        self.server_reload_btn.clicked.connect(self.server_refresh)

        # SFTP 模型 + 排序代理
        self.server_model = ServerAbstractTableModel(self.sftp)
        self.server_proxy = ServerSortFilterProxyModel(self)
        self.server_proxy.setSourceModel(self.server_model)
        # 表视图
        self.server_view = QTableView()
        self.server_view.setModel(self.server_proxy)
        self.server_view.setSortingEnabled(True)
        self.server_view.sortByColumn(6, Qt.SortOrder.AscendingOrder)
        self.server_view.doubleClicked.connect(self.on_double_click)
        self.server_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.server_view.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.server_view.setColumnWidth(0, 300)  # 设置列宽
        self.server_view.setColumnWidth(1, 100)  # 设置列宽
        self.server_view.setColumnWidth(2, 100)  # 设置列宽
        self.server_view.setColumnWidth(3, 135)  # 设置列宽
        self.server_view.setColumnWidth(4, 100)  # 设置列宽
        self.server_view.setColumnWidth(5, 100)  # 设置列宽
        self.server_view.hideColumn(6)
        self.server_view.hideColumn(7)
        QTimer.singleShot(0, self.adjust_column_widths2)
        self.server_view.setStyleSheet("""
                    QTableView {
                        border: none;
                        gridline-color: transparent;
                        outline: none;
                        selection-background-color: #e0f0ff;  /* 可自定义选中颜色 */
                    }
                    QHeaderView::section {
                        border: none;
                        background-color: transparent;
                    }
                """)

        # 右键菜单下载
        self.server_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.server_view.customContextMenuRequested.connect(self.on_context_menu)
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("远程路径"))
        hbox.addWidget(self.server_path_edit, 1)  # 输入框获得布局剩余空间
        hbox.addWidget(self.server_up_btn)  # 按钮仅占它的推荐大小
        hbox.addWidget(self.server_reload_btn)  # 按钮仅占它的推荐大小
        vbox.addLayout(hbox)
        vbox.addWidget(self.server_view)
        self.server_refresh()
        return vbox

    @Slot(QModelIndex)
    def on_double_click(self, idx: QModelIndex):
        """双击路径"""
        source_idx = self.server_proxy.mapToSource(idx)
        entry = self.server_model.server_entries[source_idx.row()]
        if entry["is_dir"]:
            if entry["symlink_target"]:
                newpath = posixpath.join(self.server_model.cwd(), entry["symlink_target"])
            else:
                newpath = posixpath.join(self.server_model.cwd(), entry["name"])
            self.server_change_dir(newpath)
        else:
            self.download_init() # 双击的时候，如果是文件直接下载

    def server_change_dir(self, path: str):
        """切换路径"""
        real_path = self.sftp.normalize('.')
        try:
            self.sftp.chdir(path)
            real = self.sftp.getcwd()
            self.server_path_edit.setText(real)
            self.server_model.refresh(real)
        except Exception as e:
            if isinstance(e,FileNotFoundError):
                QMessageBox.warning(self, "切换失败", f'目录不存在:{path}')
            self.server_path_edit.setText(real_path)

    @Slot()
    def server_on_path_enter(self):
        """路径 回车"""
        self.server_change_dir(self.server_path_edit.text().strip())

    def server_go_up(self):
        """上级目录"""
        parent = posixpath.dirname(self.server_model.cwd().rstrip("/")) or "/"
        self.server_change_dir(parent)

    @Slot()
    def on_context_menu(self, pos):
        menu = QMenu(self)
        download_action = QAction("下载", self)
        download_action.triggered.connect(self.download_init)
        menu.addAction(download_action)

        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.server_refresh)
        menu.addAction(refresh_action)

        to_up_action = QAction("上级目录", self)
        to_up_action.triggered.connect(self.server_go_up)
        menu.addAction(to_up_action)

        menu.exec(self.server_view.viewport().mapToGlobal(pos))



    @Slot()
    def server_refresh(self):
        try:
            self.server_model.refresh(self.server_path_edit.text().strip())
            self.server_view.sortByColumn(6, Qt.SortOrder.AscendingOrder)
        except Exception as e:
            QMessageBox.warning(self, "刷新失败", str(e))

    def upload_init(self, select_paths):
        """上传文件, 如果同时选中多个文件,都添加到列表中"""
        if not select_paths:
            return
        for path in select_paths:
            self.upload_add_file_to_list(path)

    def upload_add_file_to_list(self, local_file_path):
        """根据文件路径,把文件添加到列表中"""
        remote_path = self.server_path_edit.text().strip() #远程路径
        # 根据路径生成文件列表 ('文件','c:/test/1.txt','/home/admin/1.txt')
        file_list = get_folder_all_file(local_file_path,remote_path)
        if not file_list:
            return
        for file_type, local_name,remote_name in file_list:
            file_transfer_data = TransferItem(
                trans_type='上传',
                file_type=file_type,
                trans_time=get_datetime(),
                local_file=local_name,
                remote_file=remote_name,
                file_size=os.path.getsize(local_name),
                trans_size=0,
                trans_status='等待中',
                file_base_path='没用待删除'
            )
            self.file_transfer_model.add_item(file_transfer_data)

    def upload_sftp_file(self, row, file_type, local_name, remote_name):
        """真正的上传文件调用"""
        cb = lambda transferred, total_size, lf=local_name: (
            self.file_transfer_model.update_item(row, transferred, total_size)
        )
        if file_type == '文件夹':
            mk_result = self.remote_mkdir(remote_name)
            if mk_result:
                self.file_transfer_model.update_item(row, 0, 0)
            else:
                # 无法创建上级目录
                self.file_transfer_model.update_item(row, 0, 0,4)
        elif file_type == '文件':
            if not os.path.isfile(local_name):
                # 文件不存在
                self.file_transfer_model.update_item(row, 0, 0, 2)
                return
            try:
                # 检查上级目录是否存在,不存在就创建上级目录
                parent_path = Path(remote_name).parent.as_posix()
                mk_result = self.remote_mkdir(parent_path)
                if mk_result:
                    # 上传文件回调
                    self.sftp.put(local_name, remote_name, callback=cb)
                else:
                    # 无法创建上级目录
                    self.file_transfer_model.update_item(row, 0, 0, 4)
            except Exception as e:
                if isinstance(e, PermissionError):
                    # 没有对目录上传的权限
                    self.file_transfer_model.update_item(row, 0, 0, 1)
                else: # 未知异常
                    self.file_transfer_model.update_item(row, 0, 0, 3)
            # 如果文件大小为0,不能触发回调,需要手动设置一下文件上传成功
            total = os.path.getsize(local_name)
            if total == 0:
                self.file_transfer_model.update_item(row, 0, 0)

    def remote_mkdir(self, remote_dir):
        try:
            self.sftp.stat(remote_dir)
            return True
        except IOError as e:
            try:
                self.sftp.mkdir(remote_dir)
                return True
            except IOError :
                return False

    def remote_path_files_and_dirs(self,remote_path, local_path):
        """
        递归列出远程服务器指定目录及其子目录下的所有文件和文件夹
        :param remote_path: 远程目录路径
        :param local_path: 用于构建本地路径表示的前缀
        :return: 包含所有文件和文件夹路径的列表
        """
        file_list = [('文件夹', local_path, remote_path, 0)]
        try:
            # 获取远程目录下的所有条目
            entries = self.sftp.listdir_attr(remote_path)
            for entry in entries:
                entry_name = entry.filename
                entry_path = (Path(remote_path)/entry_name).as_posix()
                display_path = (Path(local_path)/entry_name).as_posix()
                # 判断是文件还是目录
                if S_ISDIR(entry.st_mode):
                    # 如果是目录，添加到列表并递归处理
                    file_list.append(('文件夹',display_path,entry_path,0))
                    # 递归处理子目录
                    sub_files = self.remote_path_files_and_dirs(entry_path,display_path)
                    file_list.extend(sub_files)
                else:
                    # 如果是文件，直接添加到列表
                    file_list.append(('文件',display_path,entry_path,entry.st_size))
        except Exception as e:
            print(f"处理路径 {remote_path} 时出错: {str(e)}")
        return file_list

    def download_init(self):
        sel = self.server_view.selectionModel().selectedRows(0)
        items = [
            self.server_model.server_entries[self.server_proxy.mapToSource(idx).row()]
            for idx in sel
        ]
        self.download_add_file_to_list(items)

    def download_add_file_to_list(self,items):
        """下载文件添加到下载队列"""
        def worker():
            for file_item in items:
                remote = Path(self.server_model.cwd()) / file_item["name"]
                local = Path(self.local_path_combobox.currentText()) / file_item["name"]
                if file_item["is_dir"]:
                    file_list = self.remote_path_files_and_dirs(remote.as_posix(), local.as_posix())
                    for file_type, local_name, remote_name, file_size in file_list:
                        file_transfer_data = TransferItem(
                            trans_type='下载',
                            file_type=file_type,
                            trans_time=get_datetime(),
                            local_file=local_name,
                            remote_file=remote_name,
                            file_size=file_size,
                            trans_size=0,
                            trans_status='等待中',
                            file_base_path=''
                        )
                        self.file_transfer_model.add_item(file_transfer_data)
                else:
                    file_transfer_data = TransferItem(
                        trans_type='下载',
                        file_type='文件',
                        trans_time=get_datetime(),
                        local_file=local.as_posix(),
                        remote_file=remote.as_posix(),
                        file_size=file_item["size"],
                        trans_size=0,
                        trans_status='等待中',
                        file_base_path=''
                    )
                    self.file_transfer_model.add_item(file_transfer_data)
        threading.Thread(target=worker, daemon=True).start()

    def download_sftp_file(self, row, file_type, local_name, remote_name):
        cb = lambda transferred, total_size, lf=local_name: (
            self.file_transfer_model.update_item(row, transferred, total_size)
        )
        if file_type == '文件夹':
            self.local_mkdir(local_name)
            self.file_transfer_model.update_item(row, 0, 0)
        elif file_type == '文件':
            Path(local_name).parent.mkdir(parents=True, exist_ok=True)
            try:
                self.sftp.get(remote_name, local_name,callback=cb)
            except Exception as e:
                if isinstance(e, PermissionError):
                    self.file_transfer_model.update_item(row, 0, 0, 1)
                raise e
            total = os.path.getsize(local_name)
            if total == 0:
                self.file_transfer_model.update_item(row, 0, 0)

    def local_mkdir(self, local_name):
        """本地创建文件夹"""
        folder = Path(local_name)
        if  not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            return True
        return False

    def trans_file_monitor(self):
        """添加文件到列中中以后, 查看列表中还有哪些需要上传下载的文件,然后上传下载"""
        # TODO 多次上传,可能会重复触发,待验证
        if self.trans_file_monitor_running:
            return
        self.trans_file_monitor_running = True
        try:
            while  self.file_transfer_model.trans_file_list:
                row_num = self.file_transfer_model.trans_file_list.pop(0)
                self.trans_check(row_num)
        except Exception as e:
            traceback.print_exc()
        self.trans_file_monitor_running = False

    def check_local_exists(self,local_name):
        p = Path(local_name)
        return p.exists()

    def check_remote_exists(self,remote_name):
        try:
            self.sftp.stat(remote_name)
            return True
        except FileNotFoundError:
            return False

    def trans_check(self,row_num):
        item = self.file_transfer_model.items[row_num]
        if not item:
            return
        trans_status=item.trans_status
        trans_type=item.trans_type
        file_type=item.file_type
        local_file=item.local_file
        remote_file=item.remote_file
        dialog_title="请关闭窗口,重新打开"
        # 验证文件是否存在
        if trans_type == '上传':
            file_exists=self.check_remote_exists(remote_file)
            dialog_title=f"远程已存在文件: {remote_file}"
        elif trans_type == '下载':
            file_exists=self.check_local_exists(local_file)
            dialog_title=f"本地已存在文件: {local_file}"
        else:
            file_exists = False
        # 如果文件存在
        if file_exists and file_type=='文件':
            # 不再弹窗提示
            if not self.trans_no_prompt:
                dialog = SftpTransConfirmDialog(dialog_title)
                dialog.exec()
                confirmed, skip_overwrite, no_prompt = dialog.get_result()
                if confirmed: # 确认按钮
                    self.trans_no_prompt = no_prompt
                    self.trans_skip_overwrite=skip_overwrite
                else: # 取消按钮
                    self.file_transfer_model.update_item(row_num, 0, 0,5)
                    return
            if self.trans_skip_overwrite=='skip':
                self.file_transfer_model.update_item(row_num, 0, 0, 6)
                return
        # 如果文件不存在,或者用户选择了覆盖,正常传输文件
        if trans_status == "等待中" and trans_type == '上传':
            self.upload_sftp_file(row_num, file_type, local_file, remote_file)
        if trans_status == "等待中" and item.trans_type == '下载':
            self.download_sftp_file(row_num, file_type, local_file, remote_file)
