from PySide6.QtCore import QObject, Slot
from utils.config_util import FreeShellConfig
class XtermConfig(QObject):

    @Slot(result=str)
    def get_mouse_left_select(self):
        mouse_left = FreeShellConfig.get('mouse_left_select')
        if not mouse_left:
            return '开启'
        return mouse_left

    @Slot(result=str)
    def get_mouse_right_paste(self):
        mouse_right = FreeShellConfig.get('mouse_right_paste')
        if not mouse_right:
            return '开启'
        return mouse_right