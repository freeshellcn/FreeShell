from PySide6.QtCore import Qt
from PySide6.QtGui import  QTextCursor
from PySide6.QtWidgets import (QDialog, QTextEdit, QVBoxLayout,
                               QPushButton, QHBoxLayout, QMessageBox)
import os
from utils.config_util import FreeShellConfig
class LicenseDialog(QDialog):
    """软件许可协议对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("软件使用许可协议")
        self.resize(800, 600)  # 设置对话框大小

        # 创建主布局
        main_layout = QVBoxLayout(self)
        # 禁用窗口关闭按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        # 创建富文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)  # 设置为只读

        # 设置富文本内容 - 软件使用协议
        license_text = """
        <h2 style="color: #2c3e50; text-align: center;">软件使用许可协议</h2>
        
        <p style="text-align: right; margin-top: 30px;">协议版本：1.0.0</p>
        
        <h3 style="color: #34495e;">1. 协议范围</h3>
        <p>本协议适用于所有用户（以下简称"用户"）使用[FreeShell]（以下简称"本软件"）的行为。用户安装、下载或使用本软件即视为接受本协议全部条款。</p>
        
        <h3 style="color: #34495e;">2. 免责声明 </h3>
        <p>2.1 本软件以 “现状”“现有” 和 “可用” 的状态免费提供给用户，开发者不提供任何形式的明示或默示担保，包括但不限于关于本软件的适用性、可靠性、安全性、准确性、无错误、无病毒、不间断运行以及满足用户特定需求的担保。。</p>
        <p>2.2 开发者不保证本软件的功能能够满足用户的所有需求，不保证本软件在运行过程中不会出现中断、延迟、错误、漏洞或数据丢失等情况，也不保证对本软件的缺陷能够进行修复或对软件进行更新维护。因软件功能限制、性能问题导致用户无法实现预期目标、遭受数据丢失、业务中断等损失的，开发者不承担任何责任。</p>
        <p>2.3 开发者不保证本软件与用户使用的所有操作系统、硬件设备、其他软件或服务具有完全的兼容性。因本软件与其他系统、设备或软件不兼容导致用户设备损坏、数据损坏或其他损失的，开发者不承担责任。</p>
        <p>2.4 尽管开发者会在合理范围内采取措施保障软件基本安全，但互联网环境存在固有风险，开发者无法完全保证本软件免受黑客攻击、病毒感染、恶意代码植入等安全威胁，也不保证用户通过本软件传输、存储的数据的安全性。因上述安全问题导致用户数据泄露、被盗用或遭受其他损失的，开发者不承担责任。</p>
        <p>2.5 使用本软件所产生的任何风险（包括但不限于数据丢失、系统崩溃、安全漏洞、信息泄露、服务器损坏等），均由用户自行承担。</p>
        <p>2.6 开发者对因使用本软件或无法使用本软件所造成的任何直接、间接、偶然、特殊或后果性损害不承担责任。</p>
        
        <h3 style="color: #34495e;">3. 第三方组件声明</h3>
        <p>3.1 本软件依赖的第三方开源项目（包括但不限于 PySide6、Paramiko、xterm.js），其版权和许可协议归各自的版权所有者所有。</p>
        
        <h3 style="color: #34495e;">4. 用户义务</h3>
        <p>4.1 用户应自行判断本软件是否符合其使用需求，并自行承担因下载、安装、使用本软件所产生的一切风险和后果，包括但不限于设备损坏、数据丢失、网络安全问题等。</p>
        <p>4.2 用户在使用本软件过程中，应遵守国家法律法规、行业规范以及第三方服务提供商的相关规定，不得利用本软件从事任何违法、违规、侵权或损害他人合法权益的活动，包括但不限于传播违法信息、侵犯他人知识产权、窃取他人数据等。若用户因违反上述规定导致自身或第三方遭受损失，开发者不承担任何责任，且用户应自行承担由此产生的全部法律责任。</p>
        <p>4.3 用户应妥善保管与本软件使用相关的账号、密码等信息，对通过其账号进行的所有操作行为负责。因用户自身原因（如账号密码泄露、操作失误等）导致的任何损失，开发者不承担责任。</p>
        
        <h3 style="color: #34495e;">5. 协议的修改与终止</h3>
        <p>5.1 本协议自用户首次启动本软件时生效，最新版本可通过官方网址获取。新协议发布后，旧协议自动失效，双方权利义务均以新协议为准。用户必须遵守本协议全部条款。</p>
        """

        self.text_edit.setHtml(license_text)
        # 滚动到开头
        self.text_edit.moveCursor(QTextCursor.MoveOperation.Start)

        # 添加到布局
        main_layout.addWidget(self.text_edit)

        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # 不同意
        self.no_button = QPushButton("不同意")
        self.no_button.setMinimumWidth(50)
        self.no_button.clicked.connect(self.no_licence)

        # 同意
        self.ok_button = QPushButton("我已阅读并同意")
        self.ok_button.setMinimumWidth(120)
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.ok_licence)
        button_layout.addWidget(self.no_button)
        button_layout.addWidget(self.ok_button)
        main_layout.addLayout(button_layout)

    def no_licence(self):
        reply = QMessageBox.question(self, "协议确认", "不同意软件使用协议,软件将会关闭. 您是否要关闭软件?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                     , QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            FreeShellConfig.update_freeshell_config('licence_read_click', False)
            self.accept()
            os._exit(0)

    def ok_licence(self):
        FreeShellConfig.update_freeshell_config('licence_read_click',True)
        self.accept()