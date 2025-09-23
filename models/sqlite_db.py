#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import sqlite3

from utils.date_util import get_datetime as dt
from controllers.config_controller import db_init

class SQLiteDB:
    def __init__(self):
        self.db_full_path =db_init()
        self.conn = sqlite3.connect(self.db_full_path)
        self.cursor = self.conn.cursor()

    def demo0(self, user_id, name=None, age=None, email=None):
        """动态更新列"""
        update_fields = []
        params = []

        if name:
            update_fields.append("name = ?")
            params.append(name)
        if age:
            update_fields.append("age = ?")
            params.append(age)
        if email:
            update_fields.append("email = ?")
            params.append(email)
        params.append(user_id)
        sql = f"UPDATE ssh_connect_info SET {', '.join(update_fields)} WHERE id = ?"
        self.cursor.execute(sql, tuple(params))
        self.conn.commit()

    def demo1(self):
        """查询结果转JSON"""
        self.cursor.execute(""" SELECT *
                                FROM main.ssh_connect_info
                            """)
        data_all = self.cursor.fetchall()
        # 获取列名
        column_names = [desc[0] for desc in self.cursor.description]
        # 转换为 JSON
        data_list = [dict(zip(column_names, data)) for data in data_all]
        return json.dumps(data_list, indent=4, ensure_ascii=False)

    ##ssh_connect_info###############################################################################################
    def query_max_seq(self, parent_id=None):
        """查询最大的seq"""
        if not parent_id:
            self.cursor.execute("""select ifnull(max(Seq), 0) as Seq
                                   FROM main.ssh_connect_info
                                   where ParentId IS NULL""")
            data_result = self.cursor.fetchone()
        else:
            self.cursor.execute("""select ifnull(max(Seq), 0) as Seq
                                   FROM main.ssh_connect_info
                                   where ParentId = ?""", (parent_id,))
            data_result = self.cursor.fetchone()
        return data_result[0]

    def query_child_pk_id_list(self, pk_id):
        self.cursor.execute("""select PKId
                               FROM main.ssh_connect_info
                               where ParentId = ?""", (pk_id,))
        data_result = self.cursor.fetchall()
        return data_result

    def query_ssh_connect_info(self):
        """查询所有连接"""
        self.cursor.execute(""" select a.PkId,
                                       a.ParentId,
                                       a.NodeType,
                                       a.NodeName,
                                       a.Seq,
                                       a.NodeAddress,
                                       a.UserName,
                                       a.NodePort,
                                       a.UserPass,
                                       a.ConnectType,
                                       a.Remark,
                                       a.CreateTime,
                                       a.UpdateTime,
                                       b.ConfigData
                                FROM main.ssh_connect_info a
                                         left join main.ssh_connect_config b ON a.PkId = b.PkId """)
        data_all = self.cursor.fetchall()
        # 获取列名
        column_names = [desc[0] for desc in self.cursor.description]
        # 转换为 JSON
        data_list = [dict(zip(column_names, data)) for data in data_all]
        return data_list

    def insert_folder(self, parent_id, node_type, node_name, seq):
        """新增连接"""
        try:
            self.cursor.execute("""
                                INSERT INTO main.ssh_connect_info (ParentId, NodeType, NodeName, Seq, CreateTime,
                                                                   UpdateTime)
                                VALUES (?, ?, ?, ?, ?, ?)""", (parent_id, node_type,
                                                               node_name, seq, dt(), dt()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(e)
            return False

    def insert_connect(self, parent_id, node_type, node_name, seq, node_address, node_port, connect_type,
                       user_name=None, user_pass=None, remark=None):
        """新增连接"""
        try:
            self.cursor.execute("""
                                INSERT INTO main.ssh_connect_info (ParentId, NodeType, NodeName, Seq, NodeAddress,
                                                                   NodePort, ConnectType, UserName, UserPass, Remark,
                                                                   CreateTime, UpdateTime)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (parent_id, node_type,
                                                                                 node_name, seq, node_address,
                                                                                 node_port, connect_type, user_name,
                                                                                 user_pass, remark, dt(), dt()))
            pk_id = self.cursor.lastrowid
            self.conn.commit()
            return pk_id
        except sqlite3.IntegrityError as e:
            print(e)
            return 0

    def update_connect(self, pk_id,parent_id, node_type, node_name, seq, node_address, node_port, connect_type,
                       user_name=None, user_pass=None):
        """新增连接"""
        try:
            self.cursor.execute("""
                                update main.ssh_connect_info  set
                                                                  ParentId=?,
                                                                  NodeType=?, 
                                                                  NodeName=?, 
                                                                  Seq=?, 
                                                                  NodeAddress=?,
                                                                  NodePort=?, 
                                                                  ConnectType=?, 
                                                                  UserName=?, 
                                                                  UserPass=?, 
                                                                  UpdateTime=? where PkId=?
                                """, (parent_id, node_type,node_name, seq, node_address,node_port,
                                      connect_type, user_name,user_pass,dt(),pk_id))
            pk_id = self.cursor.lastrowid
            self.conn.commit()
            return pk_id
        except sqlite3.IntegrityError as e:
            print(e)
            return 0

    def update_node_name(self, pkid, node_name):
        """重命名"""
        try:
            self.cursor.execute("""
                                update main.ssh_connect_info
                                set NodeName=?,
                                    UpdateTime=?
                                where PkId = ?""", (node_name, dt(), pkid))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(e)
            return False

    def update_move(self, pk_id, parent_id, seq):
        try:
            self.cursor.execute("""
                                UPDATE main.ssh_connect_info
                                set ParentId=?,
                                    Seq=?,
                                    UpdateTime=?
                                where PkId = ?""",
                                (parent_id, seq, dt(), pk_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(e)
            return False

    def delete_connect_by_pk_id_list(self, ids_param, pk_id_list):
        if not pk_id_list:
            return True  # 没有要删的，提前返回
        sql = f"DELETE FROM main.ssh_connect_info WHERE PkId IN ({ids_param})"
        self.cursor.execute(sql, pk_id_list)
        self.conn.commit()
        return True

    ##ssh_base_data###############################################################################################
    def query_base_data(self, data_code):
        self.cursor.execute("""select DataContent
                               FROM main.ssh_base_data
                               where DataCode = ?""",
                            (data_code,))
        data_result = self.cursor.fetchone()
        return data_result[0]

    def insert_base_data(self, data_code, data_content):
        try:
            self.cursor.execute("""
                                INSERT INTO main.ssh_base_data (DataCode, DataContent, CreateTime, UpdateTime)
                                VALUES (?, ?, ?, ?)""", (data_code, data_content, dt(), dt()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(e)
            return False

    def update_base_data(self, data_code, data_content):
        try:
            self.cursor.execute("""
                                UPDATE main.ssh_base_data
                                set DataContent=?,
                                    UpdateTime=?
                                where DataCode = ?""",
                                (data_content, dt(), data_code))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(e)
            return False

    def delete_base_data(self, ids_param, pk_id_list):
        if not pk_id_list:
            return True  # 没有要删的，提前返回
        sql = f"DELETE FROM main.ssh_base_data WHERE DataCode IN ({ids_param})"
        self.cursor.execute(sql, pk_id_list)
        self.conn.commit()
        return True

    ##ssh_button_info###############################################################################################

    def query_button_info_max_seq(self):
        self.cursor.execute("""
                            select ifnull(Max(Seq), 0) + 1 as Seq
                            FROM main.ssh_button_info""")
        data_result = self.cursor.fetchone()
        return data_result[0]

    def query_button_info_list(self):
        self.cursor.execute("""
                            select PkId,
                                   BtnName,
                                   BtnContent,
                                   Seq,
                                   ButtonId  
                            from main.ssh_button_info
                            order by Seq """)
        data_result = self.cursor.fetchall()
        # 获取列名
        column_names = [desc[0] for desc in self.cursor.description]
        data_list = [dict(zip(column_names, data)) for data in data_result]
        return data_list

    def insert_button_info(self, btn_name, btn_content, seq, button_id):
        try:
            self.cursor.execute("""
                                insert into main.ssh_button_info (BtnName, BtnContent, Seq, ButtonId, CreateTime, UpdateTime)
                                values (?, ?, ?, ?, ?, ?)""", (btn_name, btn_content, seq, button_id, dt(), dt()))
            pk_id = self.cursor.lastrowid
            self.conn.commit()
            return pk_id
        except sqlite3.IntegrityError as e:
            print(e)
            return -1

    def update_button_info(self, button_name, button_content, seq, button_id, pk_id_edit):
        try:
            self.cursor.execute("""
                                UPDATE main.ssh_button_info
                                set BtnName=?,
                                    BtnContent=?,
                                    Seq=?,
                                    ButtonId=?
                                where PkId = ?""",
                                (button_name, button_content, seq, button_id, pk_id_edit))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(e)
            return False

    def delete_button_info(self, pk_id):
        try:
            self.cursor.execute("""
                                delete
                                from main.ssh_button_info
                                where PkId = ?""", (pk_id,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(e)
            return False

    ##ssh_connect_config###############################################################################################
    def insert_connect_config(self, pk_id, config_data):
        try:
            self.cursor.execute("""
                                INSERT INTO main.ssh_connect_config (PkId, ConfigData, CreateTime, UpdateTime)
                                VALUES (?, ?, ?, ?)""", (pk_id, config_data, dt(), dt()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(e)
            return False

    def update_connect_config(self, pk_id, config_data):
        try:
            self.cursor.execute("""
                                UPDATE main.ssh_connect_config
                                set ConfigData=?,
                                    UpdateTime=?
                                where PkId = ?""",
                                (config_data, dt(), pk_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(e)
            return False

    def delete_connect_config(self, ids_param, pk_id_list):
        if not pk_id_list:
            return True  # 没有要删的，提前返回
        sql = f"DELETE FROM main.ssh_connect_config WHERE PkId IN ({ids_param})"
        self.cursor.execute(sql, pk_id_list)
        self.conn.commit()
        return True
