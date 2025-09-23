#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from pathlib import Path
import shutil
import importlib.resources as resources
def db_init():
    # 获取用户主目录并拼接目标目录
    free_shell_dir = Path.home() / '.FreeShell'
    # 如果目录不存在，则创建（包括所有父目录）
    free_shell_dir.mkdir(parents=True, exist_ok=True)
    # 数据库配置文件
    fsdb = free_shell_dir / 'fs.db'
    if not fsdb.is_file():
        # 从包内复制资源文件
        with resources.path('resources.db', 'init.db') as source_path:
            shutil.copy2(source_path, fsdb)
    return fsdb