import sys
import os
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread

class ManagedThread(QThread):
    _registry = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._running = True
        ManagedThread._registry.add(self)

    def stop(self):
        self._running = False
        self.wait(2000)  # 最多等 2 秒

    @classmethod
    def stop_all(cls):
        for t in list(cls._registry):
            if t.isRunning():
                t.stop()


def safe_exit(exit_code=0, force_kill=True):
    """安全退出 PySide6 应用，最后可强制杀进程"""
    for w in QApplication.topLevelWidgets():
        w.close()

    try:
        ManagedThread.stop_all()
    except Exception as e:
        pass
    # 给 UI 和线程清理一点时间
    time.sleep(0.1)

    app = QApplication.instance()
    if app:
        app.quit()

    if force_kill:
        os._exit(exit_code)  # 硬杀，保证一定退出
    else:
        sys.exit(exit_code)
