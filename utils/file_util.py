import os
from pathlib import Path
import posixpath

import os
from pathlib import Path

def get_folder_all_file(file_path, remote_base_path):
    """
    获取本地文件夹下所有子目录和文件，构造对应的远程Linux路径，
    保留本地文件夹名作为远程路径中的一部分。
    """
    if not os.path.exists(file_path):
        print(f"错误：'{file_path}' 不存在")
        return None
    all_files = []
    file_path = Path(file_path).resolve()  # 本地绝对路径
    file_name = file_path.name             # 保留最后一级文件夹名
    remote_base_path = Path(remote_base_path).as_posix()
    # 把远程根目录拼接上本地的最末目录名，作为最终远程根路径
    remote_root_path = f"{remote_base_path}/{file_name}"
    if file_path.is_file():
        all_files.append(('文件', file_path.as_posix(), Path(remote_root_path).as_posix()))
        return all_files
    elif file_path.is_dir():
        # 起始文件夹自己
        all_files.append(('文件夹',file_path.as_posix(), remote_root_path))
        for root, dirs, files in os.walk(file_path):
            root_path = Path(root)
            for dir_name in dirs:
                abs_path = root_path / dir_name
                relative = abs_path.relative_to(file_path)
                remote_path = Path(remote_root_path) / relative
                all_files.append(('文件夹', abs_path.as_posix(), remote_path.as_posix()))
            for file_name in files:
                abs_path = root_path / file_name
                relative = abs_path.relative_to(file_path)
                remote_path = Path(remote_root_path) / relative
                all_files.append(('文件', abs_path.as_posix(), remote_path.as_posix()))
        return all_files
    return None


def format_file_size(size_bytes):
    """
    将字节数转换为合适的文件大小单位

    参数:
        size_bytes: 文件大小，以字节为单位的整数

    返回:
        格式化后的字符串，包含数值和合适的单位
    """
    # 定义单位和对应的换算比例
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit = units[0]  # 初始化单位为最小单位

    # 找到最合适的单位
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            break
        size /= 1024.0

    # 根据数值大小决定保留的小数位数
    if size >= 100:
        return f"{int(round(size))} {unit}"
    elif size >= 10:
        return f"{size:.1f} {unit}"
    else:
        return f"{size:.2f} {unit}"