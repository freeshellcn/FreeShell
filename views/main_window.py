#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import json

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFontMetrics,QFont,QIcon, QAction
from PySide6.QtWidgets import (
    QTreeWidgetItem,
    QMessageBox, QLineEdit, QMainWindow, QWidget, QPushButton, QTabWidget, QDockWidget, QHBoxLayout,
    QVBoxLayout, QScrollArea, QMenu, QInputDialog, QSizePolicy, QApplication, QLabel
)
from models.sqlite_db import SQLiteDB
from views.draggable_tree import DraggableTree
from views.index_tab import IndexTab
from views.show_about_dialog import AboutDialog
from views.terminal_tab import TerminalTab
from views.connect_input_form import ConnectInputForm
from utils.icon_util import resource_path
from views.sftp_window import UpDownLoadWindow
from utils.aes_gcm import encrypt
from views.button_down_form import ButtonDownForm
from views.license_dialog import LicenseDialog
from views.setting_form import SettingForm
from controllers.exit_config import safe_exit
from views.use_third_soft import UseThirdSoftDialog
from utils.config_util import FreeShellConfig


def setting_global():
    setting = SettingForm()
    setting.exec_show()


class MainWindow(QMainWindow):
    # 类初始化
    def __init__(self):
        super().__init__()
        self.db = SQLiteDB()
        self.main_tab = QTabWidget() #主显示区域
        self.use_third_soft_dialog=UseThirdSoftDialog()
        # 优化重绘：启用双缓冲，减少闪烁
        # self.main_tab.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        # self.main_tab.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)  # 不透明绘制，减少重绘次数
        # self.main_tab.setUpdatesEnabled(True)

        # 设置QSS样式，自定义活动标签的外观
        self.main_tab.setStyleSheet("""
                   /* 所有标签的基本样式 */
                   QTabBar::tab {
                       background-color: #f0f0f0;  /* 非活动标签背景色 */
                       color: #333333;             /* 非活动标签文字色 */
                       padding: 4px 8px;          /* 内边距 */
                       margin-right: 2px;          /* 标签之间的间距 */
                       border: 1px solid #ccc;     /* 边框 */
                       border-bottom-color: #aaa;  /* 底部边框色 */
                       border-radius: 4px 4px 0 0; /* 顶部圆角 */
                   }

                   /* 活动标签的样式 */
                   QTabBar::tab:selected {
                       background-color: #1E88E5;  /* 活动标签背景色（蓝色，比较明显） */
                       color: #FFFFFF;               /* 活动标签文字色 */
                       border-color: #1565C0;      /* 活动标签边框色 */
                       border-bottom-color: #1E88E5; /* 底部边框与背景同色，看起来像融入内容区 */
                       font-weight: bold;          /* 文字加粗 */
                   }

                   /* 鼠标悬停在标签上的样式 */
                   QTabBar::tab:hover:!selected {
                       background-color: #e0e0e0;  /* 悬停时背景色 */
                   }
               """)
        self.tree = DraggableTree(self) #可拖动的tree连接信息tree
        self.index_tab = IndexTab() #首页
        self.connect_input_form = None
        self.pk_id_list = []
        self.setWindowTitle(f"FreeShell {FreeShellConfig.SOFT_VERSION}")
        self.setGeometry(100, 100, 1000, 600)  # 窗口大小
        self.setWindowIcon(QIcon(resource_path("resources/image/Logo.png")))
        self.folder_icon = QIcon(resource_path("resources/image/folder.png"))
        self.item_icon = QIcon(resource_path("resources/image/computer.png"))
        self._init_connect_tree()
        self._init_connect_tree_event()
        self._init_menu()  # 初始化菜单栏
        self._init_tool_bar()  # 初始化按钮
        self._init_main_tab()  # 主显示区域
        self._init_ui_layout()  # 主页布局
        self._init_down_button()  # 初始化底部按钮
        self._init_index()  # 加载首页
        self.sftp_windows = [] #保存所有打开的SFTP连接窗口，临时方案，以后改成字典， 给窗口生成一个ID
        self.sftp_window=None


    def _init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        # menubar.setStyleSheet("QMenuBar { background-color: #f0f0f1; }")
        file_menu = menubar.addMenu("文件(F)")
        file_menu_new_connect = file_menu.addAction(QIcon(resource_path('resources/image/link_add.png')),"新建连接")
        file_menu_new_connect.triggered.connect(self._create_connect)
        file_menu_new_folder = file_menu.addAction(QIcon(resource_path('resources/image/folder_add.png')),"新建文件夹")
        file_menu_new_folder.triggered.connect(self._create_folder)
        file_menu_exit = file_menu.addAction(QIcon(resource_path('resources/image/stop.png')),"退出程序")
        file_menu_exit.triggered.connect(self.close)  # 点击后退出程序

        view_menu = menubar.addMenu("视图(V)")
        self.view_menu_connect = QAction("连接管理", self, checkable=True)
        self.view_menu_connect.setChecked(True)
        self.view_menu_connect.triggered.connect(self.show_hide_connect)  # 连接显示状态
        view_menu.addAction(self.view_menu_connect)

        self.view_menu_index = QAction("首页", self, checkable=True)
        self.view_menu_index.setChecked(True)
        self.view_menu_index.triggered.connect(self.show_hide_index)  # 首页显示状态
        view_menu.addAction(self.view_menu_index)

        self.view_menu_button = QAction("按钮命令", self, checkable=True)
        self.view_menu_button.setChecked(FreeShellConfig.get('view_menu_button_chk'))
        self.view_menu_button.triggered.connect(self.show_hide_button)
        view_menu.addAction(self.view_menu_button)

        set_menu = menubar.addMenu("设置(S)")
        setting_global_action = set_menu.addAction("全局设置")
        setting_global_action.triggered.connect(setting_global)

        view_help = menubar.addMenu("帮助(H)")
        view_help_agreement = view_help.addAction("软件协议")
        view_help_agreement.triggered.connect(self.show_license)
        view_help_about = view_help.addAction("关于我们")
        view_help_about.triggered.connect(self.show_about)

    def _init_tool_bar(self):
        """初始化按钮栏"""
        self.toolbarMenu = self.addToolBar("按钮栏")
        self.toolbarMenu.setStyleSheet(""" 
            QToolBar { 
                background-color: #ffffff; 
            }
            QToolButton {
                border: 0px solid gray;
                border-radius: 4px;
                padding: 0px;
                margin: 0px;
            }
            QToolButton:hover {
                background-color: #e6f2ff;
            }
        """)
        # self.toolbarMenu.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)  # 显示图标+文字
        add_connect= QAction(QIcon(resource_path('resources/image/link_add.png')), "新建连接", self)
        self.toolbarMenu.addAction(add_connect)
        add_connect.triggered.connect(self._button_create_connect)

        add_folder = QAction(QIcon(resource_path('resources/image/folder_add.png')), "新建文件夹", self)
        self.toolbarMenu.addAction(add_folder)
        add_folder.triggered.connect(self._button_create_folder)

        updown_load = QAction(QIcon(resource_path('resources/image/upload.png')), "上传下载", self)
        self.toolbarMenu.addAction(updown_load)
        updown_load.triggered.connect(self._sftp_up_down_file)


    def _init_main_tab(self):
        """ 初始化QTabWidget 主显示区域 """
        # 启用标签页拖动排序
        self.main_tab.setMovable(True)
        # 为 TabBar 设置右键菜单
        self.main_tab.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.main_tab.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)
        # 显示关闭按钮
        self.main_tab.setTabsClosable(True)
        # 关闭tab
        self.main_tab.tabCloseRequested.connect(self.close_tab)
        # 右侧主要内容区域
        self.setCentralWidget(self.main_tab)

    def _init_ui_layout(self):
        """首页布局"""
        self.dock = QDockWidget("连接管理")
        self.dock.setStyleSheet("""
            QDockWidget::title {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #ccc;
            }
            QDockWidget {
                font-size: 10pt;  /* 通过字体大小间接影响高度 */
            }
        """)
        # 运行停靠的位置
        self.dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        # 允许移动,右上角有关闭按钮
        self.dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setMinimumHeight(25)
        self.search_box.setPlaceholderText("搜索连接信息")
        self.search_box.textChanged.connect(self.on_filter_text)
        # 页面布局
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.search_box)  # 添加搜索框
        self.dock.setWidget(container)
        self.layout.addWidget(self.tree)
        self._tree_default_check()
        # Dock 是否可见和菜单栏里的状态一致
        self.dock.visibilityChanged.connect(self._docker_visibility_changed)

    def on_filter_text(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            self._filter_node(self.tree.topLevelItem(i), text)

    def _filter_node(self, item, kw) -> bool:
        matched = kw in item.text(0).lower()
        any_child = False
        for j in range(item.childCount()):
            if self._filter_node(item.child(j), kw):
                any_child = True
        item.setHidden(not (matched or any_child))
        return matched or any_child

    def _docker_visibility_changed(self):
        """Dock Tree 是否可见和菜单栏里的状态一致"""
        self.view_menu_connect.setChecked(self.dock.isVisible())

    # 加载连接信息
    def _init_connect_tree(self):
        rows = self.db.query_ssh_connect_info()
        self.children = {}
        for row in rows:
            self.children.setdefault(row["ParentId"], []).append(row)
        for ParentId in self.children:
            self.children[ParentId].sort(key=lambda x: x['Seq'])
        self.tree.clear()

        def add_nodes(parent, pid):
            for row_data in self.children.get(pid, []):
                node = QTreeWidgetItem(parent, [row_data['NodeName']])
                ico = self.folder_icon if row_data['NodeType'] == 'folder' else self.item_icon
                node.setIcon(0, ico)
                node.setData(0, Qt.ItemDataRole.UserRole, row_data)
                # 文件不可放置子元素；文件夹可
                flags = node.flags() | Qt.ItemFlag.ItemIsDragEnabled
                if row_data['NodeType'] == 'folder':
                    flags |= Qt.ItemFlag.ItemIsDropEnabled
                else:
                    flags &= ~Qt.ItemFlag.ItemIsDropEnabled
                node.setFlags(flags)
                add_nodes(node, row_data['PkId'])
        add_nodes(self.tree, None)

    def _init_connect_tree_event(self):
        self.tree.itemDoubleClicked.connect(self.on_tree_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_menu)

    def _on_tree_menu(self, pos: QPoint):
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        # 在空白位置右击
        if not item:
            menu.addAction(QIcon(resource_path("resources/image/link_add.png")), "新建连接", lambda: self._create_connect(item))
            menu.addAction(QIcon(resource_path("resources/image/folder_add.png")), "新建文件夹", lambda: self._create_folder(item))
        # 文件夹右击
        elif item and item.data(0, Qt.ItemDataRole.UserRole)['NodeType'] == 'folder':
            menu.addAction(QIcon(resource_path("resources/image/link_add.png")), "新建连接", lambda: self._create_connect(item))
            menu.addAction(QIcon(resource_path("resources/image/folder_add.png")), "新建文件夹", lambda: self._create_folder(item))
            menu.addAction(QIcon(resource_path("resources/image/folder_edit.png")), "重命名", lambda: self._rename_item(item))
            menu.addAction(QIcon(resource_path("resources/image/folder_delete.png")), "删除", lambda: self._delete_item(item))
        elif item and item.data(0, Qt.ItemDataRole.UserRole)['NodeType'] == 'item':
            menu.addAction(QIcon(resource_path("resources/image/link_go.png")), "连接服务", lambda: self.on_tree_double_click(item,None))
            menu.addAction(QIcon(resource_path("resources/image/link_edit.png")), "重命名", lambda: self._rename_item(item))
            menu.addAction(QIcon(resource_path("resources/image/link_delete.png")), "删除", lambda: self._delete_item(item))
            menu.addAction(QIcon(resource_path("resources/image/link_break.png")), "编辑连接",lambda: self._edit_item(item))
        else:
            menu.addAction(QIcon(resource_path("resources/image/link_delete.png")), "数据错误，只能删除", lambda: self._delete_item(item))
        menu.exec(self.tree.mapToGlobal(pos))
    def _edit_item(self,item):
        """属性：编辑连接"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        config_data_dict = item_data["ConfigData"]
        if not config_data_dict:
            QMessageBox.warning(None, "提示信息", "连接信息错误，请重新修改连接信息")
            return
        self.connect_input_form=ConnectInputForm()
        self.connect_input_form.insert_connect.connect(self._reload_tree)
        self.connect_input_form.exec_show(title="编辑连接", data=item_data)
    def _rename_item(self, item):
        """重命名"""
        if not item:
            return
        pk_id = item.data(0, Qt.ItemDataRole.UserRole)['PkId']
        node_name = item.data(0, Qt.ItemDataRole.UserRole)['NodeName']
        name, ok = QInputDialog.getText(self, "重命名", "新名称：", QLineEdit.EchoMode.Normal, node_name)
        if not (ok and name.strip()):
            return
        self._update_node_name(pk_id,name.strip())
        self._reload_tree()

    def _delete_item(self, item):
        """删除文件夹及其子文件夹"""
        if not item:
            return
        reply = QMessageBox.question(
            self,
            "删除确认",
            "确定要删除吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return
        pk_id = item.data(0, Qt.ItemDataRole.UserRole)['PkId']
        self._fetch(pk_id)
        ids_param = ",".join("?" * len(self.pk_id_list))
        self.db.delete_connect_by_pk_id_list(ids_param, self.pk_id_list)
        self.db.delete_connect_config(ids_param, self.pk_id_list)
        self.pk_id_list = []
        self._reload_tree()

    def _fetch(self,pk_id):
        self.pk_id_list.append(pk_id)
        rows=self.db.query_child_pk_id_list(pk_id)
        child_ids = [row[0] for row in rows]
        for cid in child_ids:
            self.pk_id_list.append(cid)
            self._fetch(cid)

    def _reload_tree(self):
        """重新加载连接树的信息"""
        self.tree.clear() # 清理tree
        self._init_connect_tree() # 重新获取连接
        self.layout.invalidate() # 布局失效
        self.layout.activate() # 布局激活
        self._tree_default_check() # 设置默认选中第一个

    def _tree_default_check(self):
        first_item = self.tree.topLevelItem(0)
        if first_item:
            self.tree.setCurrentItem(first_item)

    def _button_create_folder(self):
        # item = self.tree.currentItem()
        # if item and item.data(0, Qt.ItemDataRole.UserRole)['NodeType'] == 'item':
        #     return
        self._create_folder()

    def _button_create_connect(self):
        # item = self.tree.currentItem()
        # if item and item.data(0, Qt.ItemDataRole.UserRole)['NodeType'] == 'item':
        #     return
        self._create_connect()

    def _create_connect(self,item=None):
        """创建连接"""
        self.connect_input_form=ConnectInputForm()
        self.connect_input_form.insert_connect.connect(self._reload_tree)
        if not item:
            self.connect_input_form.exec_show(title="新建连接")
        else:
            parent_id = item.data(0, Qt.ItemDataRole.UserRole)['PkId']
            self.connect_input_form.exec_show(title="新建连接",parent_id=parent_id)

    def _create_folder(self, item=None):
        """创建文件夹"""
        pid = None
        if item and item.data(0, Qt.ItemDataRole.UserRole)['NodeType'] == 'folder':
            pid = item.data(0, Qt.ItemDataRole.UserRole)['PkId']
        name, ok = QInputDialog.getText(self, "新建文件夹","名称：", QLineEdit.EchoMode.Normal, "文件夹")
        if not (ok and name.strip()):
            return
        self._insert_node(pid, 'folder', name.strip())
        self._reload_tree()

    def _insert_node(self, parent_id,node_type,node_name):
        seq = self.db.query_max_seq(parent_id)
        self.db.insert_folder(parent_id,node_type,node_name,seq)

    def _update_node_name(self, pk_id, node_name):
        self.db.update_node_name(pk_id, node_name)

    def on_tree_double_click(self, item, _column):
        """双击连接信息"""
        conn_info = item.data(0, Qt.ItemDataRole.UserRole)
        if conn_info['NodeType'] == 'folder':
            return
        user_name = conn_info["UserName"]
        if not user_name:
            input_user, ok = QInputDialog.getText(self, "输入账号", "请输入登录账户：")
            if ok and input_user.strip():
                conn_info["UserName"]=input_user
            else:
                return
        user_pass = conn_info["UserPass"]
        if not user_pass:
            input_pass, ok = QInputDialog.getText(self, "输入密码", "请输入登录密码：",echo=QLineEdit.EchoMode.Password )
            if ok and input_pass.strip():
                conn_info["UserPass"] = encrypt(input_pass)
            else:
                return

        self.add_terminal_tab(conn_info)

    def add_terminal_tab(self, connection_info):
        config_data=connection_info["ConfigData"]
        if not config_data:
            QMessageBox.warning(None, "提示信息", "连接信息错误，请重新修改连接信息")
            return
        tab = TerminalTab(connection_info)

        # 将连接名字作为标签标题
        tab_index = self.main_tab.addTab(tab, connection_info.get("NodeName", "unknow"))
        self.main_tab.setCurrentIndex(tab_index)

    def close_tab(self, index):
        """关闭tab页"""
        widget = self.main_tab.widget(index)
        tab_id = self.main_tab.tabBar().tabData(index)
        if tab_id and tab_id == "IndexPage20250101235959DATA":
            self.view_menu_index.setChecked(False)
        if widget:
            if hasattr(widget, "close_session"):
                widget.close_session()
            self.main_tab.removeTab(index)
            widget.deleteLater()

    def show_tab_context_menu(self, pos: QPoint):
        """tab页上右击菜单"""
        index = self.main_tab.tabBar().tabAt(pos)
        if index == -1:
            return
        menu = QMenu()
        action_close_current = menu.addAction("关闭当前窗口")
        action_close_all = menu.addAction("关闭全部窗口")
        action_close_left = menu.addAction("关闭左边窗口")
        action_close_right = menu.addAction("关闭右边窗口")
        action_close_other = menu.addAction("关闭其它窗口")
        action = menu.exec(self.main_tab.mapToGlobal(pos))
        if action is None:
            return
        # 关闭当前窗口
        if action == action_close_current:
            self.close_tab(index)
        # 关闭全部窗口
        elif action == action_close_all:
            count = self.main_tab.count()
            for i in range(count - 1, -1, -1):
                self.close_tab(i)
        # 关闭左边窗口
        elif action == action_close_left:
            for i in range(index - 1, -1, -1):
                self.close_tab(i)
        # 关闭右边窗口
        elif action == action_close_right:
            count = self.main_tab.count()
            for i in range(count - 1, index, -1):
                self.close_tab(i)
        # 关闭其它窗口
        elif action == action_close_other:
            count = self.main_tab.count()
            for i in range(count - 1, -1, -1):
                if i == index:
                    continue
                self.close_tab(i)

    def show_hide_connect(self, checked):
        """左边的连接显示状态和菜单按钮的选中状态一致"""
        self.dock.setVisible(checked)

    def show_hide_index(self, checked):
        """显示隐藏首页"""
        if checked:
            self._init_index()
            self.view_menu_index.setChecked(True)
        else:
            for idx in range(self.main_tab.count()):
                table_id = self.main_tab.tabBar().tabData(idx)
                if table_id == "IndexPage20250101235959DATA":
                    self.main_tab.removeTab(idx)
                    self.view_menu_index.setChecked(False)
                    break

    def _init_down_button(self):
        """底部：滚动按钮条 DockWidget"""
        self.button_dock = QDockWidget("按钮条", self)
        self.button_dock.setTitleBarWidget(QWidget())
        self.button_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(20)
        scroll.setMaximumHeight(40)

        # 按钮容器
        self.btn_container = QWidget()
        h_layout = QHBoxLayout(self.btn_container)
        h_layout.setSpacing(1)
        h_layout.setContentsMargins(1, 1, 1, 1)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.btn_container)
        self.button_dock.setWidget(scroll)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.button_dock)
        # 右键在按钮容器上添加新按钮
        self.btn_container.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_container.customContextMenuRequested.connect(self.on_down_button_menu)
        self._create_button()
        # 初始化按钮是否隐藏的状态
        self.show_hide_button(self.view_menu_button.isChecked())

    def _create_button(self):
        """创建按钮"""
        data_list = self.db.query_button_info_list()
        layout = self.btn_container.layout()
        if layout:
            while layout.count():
                layout.takeAt(0).widget().deleteLater()
        for data in data_list:
            self.create_dynamic_button(data['BtnName'],data['BtnContent'],data['PkId'],data['Seq'],data['ButtonId'])

    def on_down_button_menu(self, pos: QPoint):
        menu = QMenu(self)
        add_act = menu.addAction("添加按钮")
        if menu.exec(self.btn_container.mapToGlobal(pos)) == add_act:
            button_down = ButtonDownForm()
            button_down.insert_button_ok.connect(self.create_dynamic_button)
            button_down.exec_show("添加按钮")

    def create_dynamic_button(self, btn_name: str, btn_content: str,pk_id:int,seq:int,button_id:int):
        """动态创建按钮栏按钮"""
        btn = QPushButton(btn_name, self.btn_container)
        btn.setProperty("BtnContent", btn_content)
        btn.setProperty("PkId", pk_id)
        btn.setProperty("Seq", seq)
        btn.setProperty("ButtonId", button_id)
        btn.setProperty("BtnName", btn_name)
        font = QFont()  # 设置字体和大小
        font.setPointSize(11)
        btn.setFont(font)
        btn.setToolTip(btn_content)
        btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu) # 按钮支持右击
        btn.customContextMenuRequested.connect(self.show_button_context_menu)
        # 自适应宽度
        btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        fm = QFontMetrics(btn.font())
        text_w = fm.horizontalAdvance(btn_name)
        margin = btn.style().pixelMetric(btn.style().PixelMetric.PM_ButtonMargin) * 2
        btn.setFixedWidth(text_w + margin)
        btn.clicked.connect(lambda _, b=btn: self.btn_click_write_xterm(b))
        self.btn_container.layout().addWidget(btn)

    def show_button_context_menu(self, pos: QPoint):
        """按钮栏按钮右击,显示菜单"""
        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return
        btn_pk_id = btn.property("PkId")
        button_name = btn.property("BtnName")
        if not btn_pk_id:
            return
        menu = QMenu()
        delete_action = menu.addAction("删除")
        edit_action = menu.addAction("编辑")
        # 将按钮坐标转换为全局坐标
        global_pos = btn.mapToGlobal(pos)
        # 弹出菜单并获取选中动作
        action = menu.exec(global_pos)
        if action == delete_action:
            delete_result=self.confirm_delete(btn_pk_id)
            if delete_result:
                btn.hide()
        if action == edit_action:
            button_content = btn.property("BtnContent")
            seq = btn.property("Seq")
            button_id = btn.property("ButtonId")
            button_down = ButtonDownForm()
            button_down.update_button_ok.connect(self.update_button)
            button_down.exec_show("编辑按钮",button_name, button_content, btn_pk_id, seq, button_id)

    def update_button(self,btn_name: str, btn_content: str,pk_id:int,seq:int,button_id:int):
        """更新按钮, 先隐藏再创建"""
        # dynamic_buttons = self.btn_container.findChildren(QPushButton) # 查找按钮容易里的所有按钮
        # if dynamic_buttons:
        #     for idx, btn in enumerate(dynamic_buttons, 1):
        #         if btn.property("PkId")==pk_id: # 如果按钮的ID一样,就隐藏按钮
        #             btn.hide()
        # self.create_dynamic_button(btn_name, btn_content, pk_id, seq, button_id)
        # 修改为每次编辑按钮,把所有的按钮都删了  重新创建
        self._create_button()


    def confirm_delete(self,btn_pk_id):
        """删除按钮栏按钮"""
        reply = QMessageBox.question(
            self,
            "删除确认",
            "确定要删除按钮吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_button_info(btn_pk_id)
            return True
        return False

    def btn_click_write_xterm(self, btn: QPushButton):
        """点击按钮, 把按钮的内容写入到 xterm 控制台"""
        btn_content = btn.property("BtnContent")
        button_id = btn.property("ButtonId")
        current_index=self.main_tab.currentIndex()
        # 当前窗口没有tab结束
        if current_index == -1:
            return
        tab_id = self.main_tab.tabBar().tabData(current_index)
        # 当前窗口为首页, 不支持按钮
        if tab_id and tab_id == "IndexPage20250101235959DATA":
            return
        current_widget = self.main_tab.currentWidget()
        if isinstance(current_widget, TerminalTab):
            current_widget.write_data(btn_content)
            # TODO 以后统一换成枚举 与 button_down_form.py
            if button_id==1:
                return
            elif button_id==2:
                current_widget.write_data('\r')
            elif button_id==3:
                current_widget.write_data('\n')
            elif button_id==4:
                current_widget.write_data('\t')


    def show_hide_button(self, checked):
        """按钮栏,显示隐藏状态"""
        if checked:
            self.button_dock.show()
            self.view_menu_button.setChecked(True)
        else:
            self.button_dock.hide()
            self.view_menu_button.setChecked(False)
        FreeShellConfig.update_freeshell_config('view_menu_button_chk', checked)


    def show_use_third_soft(self):
        """使用的开源软件"""
        self.use_third_soft_dialog.exec()

    def show_license(self):
        """使用协议"""
        license_dialog = LicenseDialog(self)
        license_dialog.exec()
    def show_version_update(self):
        """显示关于对话框"""
        QMessageBox.about(self, "版本更新",
                          "暂时不支持在线更新, 需要手动在官网下载\n"
                          "官网地址: https://www.freeshell.cn"
                          )
    def show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def _init_index(self):
        """初始化首页"""
        self.index_tab = IndexTab()
        tab_index = self.main_tab.insertTab(0, self.index_tab, '首页')
        self.main_tab.setCurrentIndex(tab_index)
        self.main_tab.tabBar().setTabData(tab_index, 'IndexPage20250101235959DATA')

    def closeEvent(self, event):
        """重写关闭事件"""
        reply = QMessageBox.question(self, "退出确认", "确定要退出FreeShell吗?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                     ,QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
            QApplication.quit()
            safe_exit()
        else:
            event.ignore()


    def _sftp_up_down_file(self):
        """通过SFTP上传下载文件"""
        current_widget = self.main_tab.currentWidget()
        if isinstance(current_widget, TerminalTab):
            sftp = current_widget.get_sftp_client()
            if not sftp:
                return
            node_name = current_widget.get_node_name()
            self.sftp_window = UpDownLoadWindow(node_name,sftp)
            self.sftp_window.show()
        else:
            QMessageBox.information(self, "提示","必须先连接一台服务器")
