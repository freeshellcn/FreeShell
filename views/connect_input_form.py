#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import json

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QComboBox, QLineEdit, QFormLayout, QDialogButtonBox, QSpinBox, QMessageBox, QListWidget, QListWidgetItem,
    QStackedWidget, QGroupBox, QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QPushButton, QTableWidget, QHeaderView,
    QTableWidgetItem
)

from models.sqlite_db import SQLiteDB
from utils.aes_gcm import encrypt, decrypt
from utils.icon_util import resource_path


class PortForwardDialog(QDialog):
    """添加 / 修改端口转发规则对话框"""

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("端口转发")
        self.resize(400, 200)
        form = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.name_edit.setText('端口转发1')
        self.local_addr = QLineEdit()
        self.local_addr.setText('127.0.0.1')
        self.local_port = QSpinBox()
        self.local_port.setRange(1, 65535)
        self.local_port.setValue(80)
        self.local_port.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.remote_addr = QLineEdit()
        self.remote_addr.setText('127.0.0.1')
        self.remote_port = QSpinBox()
        self.remote_port.setRange(1, 65535)
        self.remote_port.setValue(80)
        self.remote_port.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        form.addRow("名称:", self.name_edit)
        form.addRow("本地地址:", self.local_addr)
        form.addRow("本地端口:", self.local_port)
        form.addRow("远程地址:", self.remote_addr)
        form.addRow("远程端口:", self.remote_port)

        if data:
            self.name_edit.setText(data[0])
            self.local_addr.setText(data[1])
            self.local_port.setValue(int(data[2]))
            self.remote_addr.setText(data[3])
            self.remote_port.setValue(int(data[4]))

        buttons = QDialogButtonBox((QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addWidget(buttons)

    def get_data(self):
        return [
            self.name_edit.text().strip(),
            self.local_addr.text().strip(),
            self.local_port.value(),
            self.remote_addr.text().strip(),
            self.remote_port.value()
        ]


class ConnectInputForm(QDialog):
    insert_connect = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit_data = None
        self.pk_id = None
        self.title = '连接信息'
        self.db = None
        self.setWindowTitle(self.title)
        self.resize(600, 400)
        self.parent_id = parent
        self.setWindowIcon(QIcon(resource_path("resources/image/Logo.png")))
        # 左侧列表
        self.nav_list = QListWidget()
        self.nav_list.addItem(QListWidgetItem('连接地址'))
        self.nav_list.addItem(QListWidgetItem('配置信息'))
        self.nav_list.addItem(QListWidgetItem('端口转发(隧道)'))
        self.nav_list.setFixedWidth(120)

        # 右侧堆栈 —— 先创建 pages，再建立信号连接
        self.pages = QStackedWidget()
        self.pages.addWidget(self._create_conn_page())
        self.pages.addWidget(self._create_config_page())
        self.pages.addWidget(self._create_port_page())
        # 把信号连接放在 pages 定义之后
        self.nav_list.currentRowChanged.connect(self.pages.setCurrentIndex)
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
        hbox = QHBoxLayout()
        hbox.addWidget(self.nav_list)
        hbox.addWidget(self.pages, 1)

        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox)
        vbox.addLayout(btn_layout)

    def init_edit_data(self):
        if not self.edit_data:  # 新建连接
            self.node_name.setText("新建连接")
            self.node_address.clear()
            self.node_port.setValue(22)
            self.username.clear()
            self.userpass.clear()
            self.user_chk.setChecked(True)
            self.pass_chk.setChecked(True)
            self.term_combo.setCurrentIndex(0)
            self.code_combo.setCurrentIndex(0)
            self.keepalive_num.setValue(600)
            self.keepalive_chk.setChecked(True)
            # 清空现有表格数据
            self.port_table.setRowCount(0)
        else:  # 编辑连接
            self.node_name.setText(self.edit_data["NodeName"])
            self.node_address.setText(self.edit_data["NodeAddress"])
            self.node_port.setValue(int(self.edit_data["NodePort"]))
            self.username.setText(self.edit_data["UserName"])
            ps = self.edit_data["UserPass"]
            if ps:
                self.userpass.setText(decrypt(self.edit_data["UserPass"]))
            config_data_dict = self.edit_data["ConfigData"]
            if config_data_dict:
                config_data = json.loads(config_data_dict)
                self.user_chk.setChecked(config_data["user_chk"])
                self.pass_chk.setChecked(config_data["pass_chk"])
                self.term_combo.setEditText(config_data["term_combo"])
                self.code_combo.setEditText(config_data["code_combo"])
                self.keepalive_num.setValue(config_data["keepalive_num"])
                self.keepalive_chk.setChecked(config_data["keepalive_chk"])
                tunnel_data = config_data.get("tunnel_data")
                if tunnel_data:
                    self.json_to_table(tunnel_data)

    def _create_conn_page(self):
        conn_group = QGroupBox("连接地址")
        form = QFormLayout(conn_group)
        self.node_name = QLineEdit()
        self.node_address = QLineEdit()
        self.node_port = QSpinBox()
        self.node_port.setRange(1, 65535)
        self.node_port.setValue(22)
        self.node_port.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.username = QLineEdit()
        self.userpass = QLineEdit()
        self.user_chk = QCheckBox("记住账号")
        self.user_chk.setChecked(True)
        self.pass_chk = QCheckBox("记住密码")
        self.pass_chk.setChecked(True)
        self.node_name.setPlaceholderText("连接名称，自定义")
        self.node_address.setPlaceholderText("主机的IP地址或者主机名")
        self.username.setPlaceholderText("登录服务器的账号")
        self.userpass.setPlaceholderText("登录服务器的密码")
        self.userpass.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("连接名称:", self.node_name)
        form.addRow("主机地址:", self.node_address)
        form.addRow("主机端口:", self.node_port)
        # 把复选框放在同一行
        hb_user = QHBoxLayout()
        hb_user.addWidget(self.username)
        hb_user.addWidget(self.user_chk)
        form.addRow("登录账户:", hb_user)
        hb_pwd = QHBoxLayout()
        hb_pwd.addWidget(self.userpass)
        hb_pwd.addWidget(self.pass_chk)
        form.addRow("登录密码:", hb_pwd)

        conn_group.setLayout(form)
        return conn_group

    def _create_config_page(self):
        conf_group = QGroupBox("配置信息")
        form = QFormLayout(conf_group)
        # xterm 下拉
        self.term_combo = QComboBox()
        self.term_combo.addItems(["xterm", "xterm-256color", "vt100", "vt220"])
        form.addRow("终端选择:", self.term_combo)
        self.code_combo = QComboBox()
        self.code_combo.addItems(["UTF-8", "GBK", "Big5", "GB18030", "GB2312", "ISO-8859-1", "UTF-16", "UTF-32"])
        form.addRow("终端编码:", self.code_combo)

        # 心跳监测
        hb_layout = QHBoxLayout()
        self.keepalive_num = QSpinBox()
        self.keepalive_num.setRange(1, 36000)
        self.keepalive_num.setValue(600)
        self.keepalive_num.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.keepalive_chk = QCheckBox("启用")
        self.keepalive_chk.setChecked(True)
        hb_layout.addWidget(self.keepalive_num)
        hb_layout.addWidget(QLabel("秒 ,无操作连接不会断开"))
        hb_layout.addWidget(self.keepalive_chk)
        form.addRow("心跳检测:", hb_layout)
        return conf_group

    def _create_port_page(self):
        port_group = QGroupBox("端口转发(隧道)")
        v = QVBoxLayout(port_group)
        # 按钮行
        btn_h = QHBoxLayout()
        add_btn = QPushButton("添加");
        add_btn.clicked.connect(self.on_port_add)
        edit_btn = QPushButton("修改");
        edit_btn.clicked.connect(self.on_port_edit)
        del_btn = QPushButton("删除");
        del_btn.clicked.connect(self.on_port_delete)
        tunnel_tips = QLabel('如果[修改]或[删除]信息,需要重启FreeShell才能生效')
        tunnel_tips.setStyleSheet("color: red;")
        btn_h.addWidget(add_btn)
        btn_h.addWidget(edit_btn)
        btn_h.addWidget(del_btn)
        btn_h.addStretch()
        v.addWidget(tunnel_tips)
        v.addLayout(btn_h)
        # 表格
        self.port_table = QTableWidget(0, 5)
        self.port_table.setHorizontalHeaderLabels(
            ["名称", "本地地址", "本地端口", "远程地址", "远程端口"]
        )
        # 隐藏垂直表头（行号）
        self.port_table.verticalHeader().setVisible(False)
        self.port_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v.addWidget(self.port_table)
        return port_group

    def on_port_add(self):
        port_dialog = PortForwardDialog(self)
        if port_dialog.exec() == QDialog.DialogCode.Accepted:
            row_data = port_dialog.get_data()
            if all(row_data):
                row = self.port_table.rowCount()
                self.port_table.insertRow(row)
                for col, text in enumerate(row_data):
                    self.port_table.setItem(row, col, QTableWidgetItem(str(text)))
            else:
                QMessageBox.warning(self, "输入错误", "请填写所有字段")

    def on_port_edit(self):
        row = self.port_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中一行")
            return
        data = [self.port_table.item(row, c).text() for c in range(5)]
        dlg = PortForwardDialog(self, data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            for c, val in enumerate(dlg.get_data()):
                self.port_table.setItem(row, c, QTableWidgetItem(str(val)))

    def on_port_delete(self):
        row = self.port_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中一行")
            return
            # 显示确认对话框
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除当前内容吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,  # 提供的按钮
            QMessageBox.StandardButton.No  # 默认选中的按钮
        )

        # 根据用户选择执行操作
        if reply == QMessageBox.StandardButton.Yes:
            self.port_table.removeRow(row)

    def table_to_json(self):
        """将表格数据转换为JSON字符串"""
        data = []
        # 遍历表格的每一行
        for row in range(self.port_table.rowCount()):
            row_data = {}
            # 遍历每一列
            for col in range(self.port_table.columnCount()):
                # 获取列标题作为键
                header = self.port_table.horizontalHeaderItem(col).text()
                # 获取单元格内容作为值
                item = self.port_table.item(row, col)
                row_data[header] = item.text() if item else ""
            data.append(row_data)
        # 转换为JSON字符串
        return json.dumps(data, ensure_ascii=False, indent=2)

    def json_to_table(self, json_str):
        """从JSON字符串加载数据到表格"""
        try:
            # 清空现有表格数据
            self.port_table.setRowCount(0)

            # 解析JSON数据
            data = json.loads(json_str)

            # 遍历数据并添加到表格
            for row_data in data:
                row = self.port_table.rowCount()
                self.port_table.insertRow(row)
                # 遍历每个字段并设置到对应单元格
                for col, header in enumerate(["名称", "本地地址", "本地端口", "远程地址", "远程端口"]):
                    value = row_data.get(header, "")
                    self.port_table.setItem(row, col, QTableWidgetItem(str(value)))

        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
        except Exception as e:
            print(f"导入数据出错: {e}")

    def on_save(self):
        parent_id = self.parent_id
        node_type = "item"
        connect_type = 'ssh'  # 默认都是SSH连接
        node_name = self.node_name.text()
        if not node_name.strip():
            QMessageBox.warning(self, "提示信息", "连接名称不能为空")
            return
        node_address = self.node_address.text()
        if not node_address.strip():
            QMessageBox.warning(self, "提示信息", "主机地址不能为空")
            return
        node_port = self.node_port.value()
        if not node_port:
            QMessageBox.warning(self, "提示信息", "主机端口不能为空")
            return

        username = self.username.text()
        userpass = self.userpass.text()
        user_chk = self.user_chk.isChecked()
        pass_chk = self.pass_chk.isChecked()
        if user_chk and not username:
            QMessageBox.warning(self, "提示信息", "登录账户不能为空")
            return
        if not user_chk:
            username = None

        if pass_chk and not userpass:
            QMessageBox.warning(self, "提示信息", "登录密码不能为空")
            return
        if not pass_chk:
            userpass = None
        if userpass:
            userpass = encrypt(userpass)
        term_combo = self.term_combo.currentText()
        code_combo = self.code_combo.currentText()
        keepalive_num = self.keepalive_num.value()
        keepalive_chk = self.keepalive_chk.isChecked()
        tunnel_data = self.table_to_json()  # 端口转发信息
        data_dict = {"user_chk": user_chk, "pass_chk": pass_chk, "term_combo": term_combo, "code_combo": code_combo,
                     "keepalive_num": keepalive_num, "keepalive_chk": keepalive_chk, "tunnel_data": tunnel_data}
        self.db = SQLiteDB()

        data_content = json.dumps(data_dict, ensure_ascii=False)
        if not self.pk_id:  # 没有pk_id, 新增数据，否则编辑数据
            if not parent_id:
                seq = self.db.query_max_seq()
            else:
                seq = self.db.query_max_seq(parent_id)
            self.pk_id = self.db.insert_connect(parent_id, node_type, node_name, seq, node_address, node_port,
                                                connect_type
                                                , username, userpass)
            self.db.insert_connect_config(self.pk_id, data_content)
        else:
            self.db.update_connect(self.pk_id, parent_id, node_type, node_name, self.edit_data['Seq'], node_address,
                                   node_port,
                                   connect_type, username, userpass)
            self.db.update_connect_config(self.pk_id, data_content)
        self.accept()  # 关闭
        self.insert_connect.emit()

    def exec_show(self, title="连接信息", parent_id=None, data=None):
        self.parent_id = parent_id
        self.setWindowTitle(title)
        self.edit_data = data
        self.init_edit_data()
        if data:
            self.pk_id = data["PkId"]
        else:
            self.pk_id = None
        return self.exec()
