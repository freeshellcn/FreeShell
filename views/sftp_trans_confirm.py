from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QRadioButton,
    QCheckBox, QPushButton, QLabel, QMessageBox
)
import sys

class SftpTransConfirmDialog(QDialog):
    def __init__(self,confirm_info:str):
        super().__init__()
        self.setWindowTitle("文件传输确认")
        self.setMinimumWidth(400)
        # 主布局
        layout = QVBoxLayout()
        # 信息标签
        layout.addWidget(QLabel(confirm_info))

        # 单选框
        self.radio_skip = QRadioButton("跳过")
        self.radio_overwrite = QRadioButton("覆盖")
        self.radio_skip.setChecked(True)  # 默认选中

        layout.addWidget(self.radio_skip)
        layout.addWidget(self.radio_overwrite)

        # 复选框
        self.checkbox_no_prompt = QCheckBox("不再提示")
        layout.addWidget(self.checkbox_no_prompt)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton("确认")
        self.btn_ok.setMaximumWidth(100)
        self.btn_ok.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setMaximumWidth(100)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setDefault(True)
        button_layout.addWidget(self.btn_cancel)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_result(self):
        """返回选择的操作和复选框状态"""
        if self.result() == 1:
            skip_overwrite = "skip" if self.radio_skip.isChecked() else "overwrite"
            no_prompt = self.checkbox_no_prompt.isChecked()
            return True, skip_overwrite, no_prompt
        else:
            return False, None, None

