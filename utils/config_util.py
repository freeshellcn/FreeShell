import json
import sys

from models.sqlite_db import SQLiteDB


class FreeShellConfig:
    SYSTEM_TYPE=None
    SOFT_VERSION="0.1.1"
    if sys.platform.startswith("win"):
        SYSTEM_TYPE="windows"

    class ScreenSize:
        WIDTH = 160
        HEIGHT = 40

    @classmethod
    def update_screen_width(cls,width:int):
        cls.ScreenSize.WIDTH = width

    @classmethod
    def update_screen_height(cls, height:int):
        cls.ScreenSize.HEIGHT = height

    config_dict = {}
    def __init__(self):
        self.db=SQLiteDB()
        data = self.db.query_base_data("freeshell_config")
        if not data:
            FreeShellConfig.config_dict= {"view_menu_button_chk": True}
            self.db.insert_base_data("freeshell_config",json.dumps(self.config_dict))
        if data:
            FreeShellConfig.config_dict=json.loads(data)

    @classmethod
    def get(cls,key):
        return cls.config_dict.get(key)

    @classmethod
    def update_freeshell_config(cls, key, value):
        try:
            db = SQLiteDB()
            data_config = cls.config_dict.copy()
            data_config[key] = value
            db.update_base_data('freeshell_config', json.dumps(data_config))
            cls.config_dict = data_config
        except json.JSONDecodeError as e:
            print(f"配置解析失败: {e}")
        except Exception as e:
            print(f"更新配置失败: {e}")

config_config=FreeShellConfig()