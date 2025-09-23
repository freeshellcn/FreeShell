import os
import sys
from functools import lru_cache
from PySide6.QtGui import QIcon

# 图标资源所在目录（相对于项目根目录）
_ICON_DIR = "resources/image"

# 后缀到图标文件名的映射
_SUFFIX_ICON_MAP = {
    # 压缩包
    ".zip":  "zip.png", ".rar":  "zip.png", ".tar":   "zip.png",
    ".gz":   "zip.png", ".7z":   "zip.png", ".gzip":  "zip.png",
    ".tgz":  "zip.png", ".txz":  "zip.png", ".taz":   "zip.png",
    ".biz":  "zip.png", ".iso":  "zip.png", ".xz":    "zip.png",

    # Python
    ".py":   "pyc.ico", ".pyc":  "pyc.ico",

    # 配置文件
    ".ini":  "ini.png", ".conf": "conf.png", ".properties": "properties.png",
    ".yml":  "yml.png", ".yaml": "yml.png",  ".config"    : "conf.png",

    # Office 文档
    ".ppt":  "pptx.png", ".pptx": "pptx.png",
    ".doc":  "docx.png", ".docx": "docx.png",
    ".xls":  "xlsx.png", ".xlsx": "xlsx.png", ".csv": "xlsx.png",

    # 文本、日志
    ".txt":  "txt.png", ".log":  "txt.png",

    # 脚本 / 代码
    ".bat":  "bat.png", ".sh":   "sh.png",   ".bash": "sh.png",
    ".c":    "c.png",   ".cpp":  "cc.png",   ".java": "java.png",
    ".class":"java.png", ".jar": "java.png", ".sql":  "sql.png",
    ".js":   "js.png",  ".ts":   "ts.png",   ".tsx": "ts.png",
    ".css":  "css.png", ".json": "json.png", ".xml":  "xml.png",
    ".vue":  "vue.png", ".html": "html.png", ".htm": "html.png",
    ".mht":  "html.png", ".shtml":"html.png",".war": "java.png",
    ".mhtml": "html.png",".mhtm": "html.png",


    # 图像
    ".gif":  "gif.png", ".png":  "gif.png",  ".jpg":  "gif.png",
    ".jpeg": "gif.png", ".ico":  "gif.png",  ".icon": "gif.png",
    ".bmp":  "gif.png", ".apng": "gif.png",  ".svg":  "svg.png",

    # 多媒体
    ".mp4":  "mp4.png", ".avi":  "mp4.png", ".wmv":  "mp4.png",
    ".mov":  "mp4.png", ".mkv":  "mp4.png", ".mpeg": "mp4.png",
    ".flv":  "mp4.png", ".rmvb": "mp4.png", ".3gp":  "mp4.png",
    ".webm": "mp4.png", ".mxf":  "mp4.png", ".prores":"mp4.png",
    ".mp3":  "mp3.png", ".wav":  "mp3.png", ".aac":  "mp3.png",
    ".flac": "mp3.png", ".wma":  "mp3.png", ".ape":  "mp3.png",
    ".ogg":  "mp3.png",

    # 其他
    ".pdf":  "pdf.png", ".md":   "md.png",   ".lock": "lock.png",
    ".tmp":  "tmp.png", ".temp": "tmp.png",  ".swp" : "swp.png",
    ".pid":  "pid.png", ".so":   "bin.png",  ".rb"  : "ruby.png",
    ".rpm":  "rpm.png", ".bak":  "bak.png",  ".h"   : "h.png",
    ".php":  "php.png", ".bin":  "bin.png",  ".exe" : "exe.png",
    ".msi":  "msi.png",

    # 文件名比较长
    "template": "template.png",".error":"error.png",
}


@lru_cache(maxsize=None)
def get_icon(suffix: str) -> QIcon | None:
    """
    根据文件后缀返回对应的 QIcon。后缀不区分大小写，
    若映射中不存在，则返回 None。

    :param suffix: 带点的后缀名，如 ".txt"
    :return: QIcon 对象或 None
    """
    key = suffix.lower()
    filename = _SUFFIX_ICON_MAP.get(key)
    if not filename:
        return None

    full_path = resource_path(f"{_ICON_DIR}/{filename}")
    return QIcon(full_path)


def resource_path(relative_path: str) -> str:
    """
    返回打包后或未打包时，资源文件的绝对路径
    """
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)