#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @Author  : zhangyunjie

import codecs
import contextlib
import json
import socket
import threading
import time

import paramiko
import select
from PySide6.QtCore import QObject, Signal, Slot
from utils.config_util import FreeShellConfig as config
from utils.aes_gcm import decrypt


class SSHManager(QObject):
    receive_ssh = Signal(str)
    receive_error_data = Signal(str)
    read_error_data = Signal(str)

    def __init__(self, connect_info):
        super().__init__()
        self.threads = []
        self._stop_event = threading.Event()
        self.channel = None
        self.connect_info = connect_info
        self.config_data_dict = self.connect_info["ConfigData"]
        self.config_data = json.loads(self.config_data_dict)
        self.client = paramiko.SSHClient()
        """
           AutoAddPolicy 自动接受并添加新主机密钥
           RejectPolicy()	拒绝不认识的主机（默认行为）
           WarningPolicy()	打印警告，但允许连接
           继承 paramiko.MissingHostKeyPolicy 并自定义行为
       """
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        threading.Thread(target=self.connect_ssh).start()

    def connect_ssh(self):

        try:
            user_pass = self.connect_info["UserPass"]
            user_pass = decrypt(user_pass)
            self.client.connect(
                hostname=self.connect_info["NodeAddress"],
                port=self.connect_info["NodePort"],
                username=self.connect_info["UserName"],
                password=user_pass,
                timeout=10
            )
            self.channel = self.client.get_transport().open_session()
            term_combo = self.config_data["term_combo"]
            self.channel.get_pty(term=term_combo, width=config.ScreenSize.WIDTH, height=config.ScreenSize.HEIGHT)  # 支持Python虚拟环境名称显示
            self.channel.invoke_shell()
            if self.config_data["keepalive_chk"]:
                self.keepalive(self.config_data["keepalive_num"])
            code_comb = self.config_data['code_combo']

            threading.Thread(target=self.read_output, args=(code_comb,), daemon=True).start()
            threading.Thread(target=self.start, daemon=True).start()
        except Exception as e:
            print(e)
            self.receive_error_data.emit(str(e))

    # 设置 keepalive 心跳，每 30 秒发送一个 null 包, 防止长时间不用断开连接
    def keepalive(self, keepalive_num):
        self.client.get_transport().set_keepalive(keepalive_num)

    # 读取Linux服务器返回结果
    def read_output(self, code_comb='utf-8'):
        decoder = codecs.getincrementaldecoder(code_comb)(errors="replace")
        while True:
            data = self.channel.recv(1024)
            if data:
                text = decoder.decode(data)
                self.receive_ssh.emit(text)
            time.sleep(0.01)

    # 接收xterm里输入的命令, 在这里发给Linxu服务器
    @Slot(str)
    def send_ssh(self, data):
        if self.channel:
            try:
                self.channel.send(data)
            except Exception as e:
                print(e)
                self.receive_error_data.emit('连接已断开,请重新连接')

    # 窗口大小改变,重新调整终端大小
    @Slot(int, int)
    def resize_pty(self, width, height):
        if self.channel:
            self.channel.resize_pty(width, height)

    def get_sftp_client(self):
        """获取SFTP连接"""
        if self.channel:
            return self.client.open_sftp()
        return None

    def start(self) -> None:
        """启动端口转发，增加规则校验"""
        if not self.client or not self.channel:
            return
        tunnel_data_str = self.config_data['tunnel_data']
        if not tunnel_data_str:
            return
        tunnel_data = json.loads(tunnel_data_str)
        if not tunnel_data:
            return
        for rule in tunnel_data:
            local_ip = rule['本地地址']
            local_port = int(rule['本地端口'])
            remote_host = rule['远程地址']
            remote_port = int(rule['远程端口'])
            # 校验端口有效性
            if not (1 <= local_port <= 65535 and 1 <= remote_port <= 65535):
                continue
            # 启动转发线程
            t = threading.Thread(
                target=self._forward_tunnel,
                args=(local_ip, local_port, remote_host, remote_port),
                daemon=True
            )
            t.start()
            self.threads.append(t)

    def stop(self) -> None:
        """停止所有资源，确保安全释放"""
        if self._stop_event.is_set():
            return  # 避免重复停止

        self._stop_event.set()

        # 关闭终端通道
        if self.channel:
            try:
                self.channel.close()
            except Exception as e:
                pass

        # 关闭SSH客户端
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                pass
        # 等待线程结束
        for t in self.threads:
            if t.is_alive():
                t.join(timeout=2)  # 超时2秒强制放弃
        self.threads.clear()

    def _forward_tunnel(self, local_ip: str, local_port: int, remote_host: str, remote_port: int) -> None:
        """端口转发隧道，强化socket异常处理"""
        try:
            with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as server_sock:
                server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_sock.bind((local_ip, local_port))
                server_sock.listen(5)  # 降低backlog，避免资源浪费

                while not self._stop_event.is_set():
                    # 等待连接（超时1秒，便于响应停止信号）
                    rlist, _, _ = select.select([server_sock], [], [], 1)
                    if not rlist:
                        continue  # 超时，检查是否需要停止

                    client_sock, addr = server_sock.accept()

                    # 建立远程通道
                    try:
                        transport = self.client.get_transport() if self.client else None
                        if not transport or not transport.is_active():
                            raise RuntimeError("SSH传输通道已关闭")

                        chan = transport.open_channel(
                            "direct-tcpip",
                            (remote_host, remote_port),
                            addr
                        )
                    except Exception as e:
                        client_sock.close()
                        continue

                    # 启动数据转发线程
                    threading.Thread(
                        target=self._pipe,
                        args=(client_sock, chan),
                        daemon=True
                    ).start()

        except Exception as e:
            pass

    def _pipe(self, src: socket.socket, dst: paramiko.Channel) -> None:
        """数据转发管道，强化异常处理和资源释放"""
        with contextlib.closing(src), contextlib.closing(dst):  # 确保自动关闭
            try:
                while not self._stop_event.is_set():
                    # 等待数据（超时1秒，便于响应停止信号）
                    r, _, _ = select.select([src, dst], [], [], 1)
                    if not r:
                        continue  # 超时，检查是否需要停止

                    # 从src读取并发送到dst
                    if src in r:
                        data = src.recv(4096)  # 增大缓冲区，减少IO次数
                        if not data:
                            break  # 连接关闭
                        dst.sendall(data)  # 使用sendall确保数据完整发送

                    # 从dst读取并发送到src
                    if dst in r:
                        data = dst.recv(4096)
                        if not data:
                            break  # 连接关闭
                        src.sendall(data)

            except Exception as e:
                pass
