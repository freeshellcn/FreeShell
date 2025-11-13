from PySide6.QtWebEngineWidgets import QWebEngineView
class QWebEngineViewOverride(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()  # 改用视图级方法获取菜单
        actions_mapping = {
            "Back": "后退",
            "Forward": "前进",
            "Stop": "停止",
            "Reload": "刷新",
            "Cut": "剪切",
            "Copy": "复制 Ctrl  + Ins",
            "Paste": "粘贴 Shift + Ins",
            "Undo": "撤销",
            "Redo": "重做",
            "Select all": "全选",
            "Save page": "保存页面",
            "Save image": "保存图片",
            "Copy image": "复制图片",
            "View page source": "查看源码",
            "Paste and match style":"粘贴并匹配样式",
            "Open link in new tab": "在新标签页打开链接",
            "Open link in new window": "在新窗口打开链接",
            "Save link": "保存链接",
            "Copy link address": "复制链接地址",
            "Copy image address": "复制图片链接地址",
            "Inspect": "检查元素",
            "Open link": "打开链接",
            "Open link in private window": "在隐私窗口打开链接",
            "Download": "下载"
        }

        for action in menu.actions():
            if action.text() in actions_mapping:
                action.setText(actions_mapping[action.text()])
        menu.exec(event.globalPos())