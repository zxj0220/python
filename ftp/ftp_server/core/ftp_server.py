#!/usr/bin/python3
# !_*_coding:utf-8_*_
# __author__:"zxj"

import socketserver
import configparser
from conf import settings
import os, subprocess
import hashlib
import re
import json

STATUS_CODE = {
    200: "Task finished",  # 任务完成
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",  # 命令格式错误
    251: "Invalid cmd ",  # 无效命令
    252: "Invalid auth data",  # 身份验证数据无效
    253: "Wrong username or password",  # 用户名或密码错误
    254: "Passed authentication",  # 通过认证
    255: "Filename doesn't provided",  # 文件名未提供
    256: "File doesn't exist on server",  # 文件不存在
    257: "ready to send file",  # 准备发送文件
    258: "md5 verification",  # md5验证成功
    259: "path doesn't exist on server",  # 文件路径错误
    260: "path changed",  # 路径已更改
    261: "A file with the same name exists",  # 同名文件以存在
}


class FTPHandler(socketserver.BaseRequestHandler):
    """
    server端请求处理类。
    实例化每一个到server端的连接，并且必须重写handle()方法来实现与客户机的通信。
    """

    def setup(self):
        # 在handle之前自动执行
        print("新连接:", self.client_address)  # 输出客户的IP

    def handle(self):
        """处理请求类"""
        # self.request 是连接到客户端的TCP套接字
        while True:
            try:
                self.data = self.request.recv(1024).strip()  # 接收客户的发送的信息/请求 strip()移除多余空格
                print(self.client_address[0])
                print(self.data)
                if not self.data:
                    print(self.client_address, "断开了")
                    break

                data = json.loads(self.data.decode("utf-8"))  # 读取客户端请求
                if data.get('action') is not None:  # 如果action对应的值不为空
                    action = data.get('action')
                    if hasattr(self, "_{}".format(action)):  # 判断命令对应的函数是否存在
                        func = getattr(self, "_{}".format(action))
                        func(data)  # 调用对应的函数，将data作为参数传入
                    else:
                        print(STATUS_CODE[251])
                        self.send_response(251)  # 命令不存在，返回给客户端251状态码
                else:
                    print(STATUS_CODE[250])
                    self.send_response(250)  # action对应的值为空，命令格式错误，返回给客户端

            except ConnectionResetError as e:  # 捕获连接重置错误，比如客户端意外断开
                print("error", e)
                break

    def _auth(self, *args, **kwargs):
        """用户身份验证"""
        data = args[0]
        if data.get("username") is None or data.get("password") is None:  # 如果用户名和密码为空，返回252，身份验证数据无效
            self.send_response(252)

        user = self.authenticate(data.get("username"), data.get("password"))  # 调用authenticate()，获取返回值username
        if user is None:  # 如果user为空，说明用户名或密码错误，返回253
            self.send_response(253)
        else:
            print("passed authentication", user)
            self.user = user
            self.user['username'] = data.get("username")
            self.home_dir = "{}/home/{}".format(settings.BASE_DIR, data.get("username"))
            # 用户家目录，写死了，还需要改进，应该写到配置文件中**
            self.current_dir = self.home_dir  # 设置当前目录为用户家目录
            self.send_response(254)  # 用户身份验证成功，返回254

    def authenticate(self, username, password):
        """验证用户合法性，合法就返回用户数据"""

        config = configparser.ConfigParser()
        config.read(settings.ACCOUNT_FILE)  # 初始化实例，读取配置文件
        if username in config.sections():  # 如果配置文件中存在当前username
            _password = config[username]["Password"]
            if _password == password:  # 判断密码是否一致
                print("pass auth..", username)
                config[username]["Username"] = username
                return config[username]

    def send_response(self, status_code, data=None):
        """向客户返回数据类"""
        response = {'status_code': status_code,  # 返回状态码
                    'status_msg': STATUS_CODE[status_code],  # 返回状态码对应的描述
                    }
        if data:
            print("goes here....")
            response.update({'data': data})  # 传输数据时使用
        print("-->data to client", response)
        self.request.send(json.dumps(response).encode())  # 将返回值、描述和数据发送给客户端

    def run_cmd(self, cmd):
        cmd_res = subprocess.getstatusoutput(cmd)  # 获取shell命令的输出结果
        return cmd_res

    def _listdir(self, *args, **kwargs):
        """列出当前目录，ls命令"""
        print(args)
        if args[0]['path']:
            res = self.run_cmd("ls -lsh {}/{}".format(self.current_dir, args[0]['path']))  # 返回`ls -lsh '当前路径'` 命令执行的结果
        else:
            res = self.run_cmd("ls -lsh {}".format(self.current_dir))  # 返回`ls -lsh` 命令执行的结果
        self.send_response(200, data=res)  # 将执行结果发送给客户端，200表示执行成功

    def _change_dir(self, *args, **kwargs):
        """切换目录"""
        # print( args,kwargs)
        if args[0]:
            if args[0]['path'] == '/':
                dest_path = self.home_dir
            else:
                dest_path = "{}/{}".format(self.current_dir, args[0]['path'])
                # dest_path目标路径 = 当前路径+用户输入的路径，这里逻辑有问题,不应该直接加**
        else:
            dest_path = self.home_dir  # 如果用户未输入新路径，则返回用户的家目录
        # print("dest path", dest_path)

        real_path = os.path.realpath(dest_path)  # 获取真实路径，没啥用
        print("real path ", real_path)
        if real_path.startswith(self.home_dir):  # 检查路径是否以用户的家目录开头
            if os.path.isdir(real_path):  # 检查目录是否存在
                self.current_dir = real_path  # 修改当前目录为新路径
                current_relative_dir = self.get_relative_path(self.current_dir)  # 执行get_relative_path()，返回当前相对路径
                self.send_response(260, {'current_path': current_relative_dir})  # 将当前相对路径发送给客户端，260表示切换成功
            else:
                self.send_response(259)  # 259表示路径不存在
        else:
            print("has no permission....to access ", real_path)  # 路径不是以用户的家目录开头，无权访问，直接返回当前相对路径
            current_relative_dir = self.get_relative_path(self.current_dir)
            self.send_response(260, {'current_path': current_relative_dir})

    def get_relative_path(self, abs_path):
        """返回此用户的相对路径"""
        relative_path = re.sub("^{}".format(settings.BASE_DIR), '', abs_path)  # 判断路径是否以BASE_DIR开头
        # if not relative_path:  # 如果路径不是以BASE_DIR开头，表示相对路径等于家目录
        #     relative_path = abs_path
        print(("relative path", relative_path, abs_path))
        return relative_path  # 返回相对路径

    def _pwd(self, *args, **kwargs):
        """查看当前相对路径"""
        current_relative_dir = self.get_relative_path(self.current_dir)
        self.send_response(200, data=current_relative_dir)

    def _get(self, *args, **kwargs):
        """客户端从服务器下载文件"""
        data = args[0]
        if data.get('filename') is None:  # 如果文件名为空，发送255给客户端
            self.send_response(255)
        # user_home_dir = "%s/%s" %(settings.USER_HOME,self.user["Username"])  # 获取用户家目录，不应该写在这里，需要改进**
        file_abs_path = "{}/{}".format(self.current_dir, data.get('filename'))  # 获取文件路径
        print("file abs path", file_abs_path)

        if os.path.isfile(file_abs_path):  # 判断文件是否存在
            file_size = os.path.getsize(file_abs_path)  # 获取文件大小
            self.send_response(257, data={'file_size': file_size})  # 将文件大小发送给客户端，257表示准备发送文件
            self.request.recv(1)  # 等待客户端确认
            with open(file_abs_path, "rb") as file_obj:  # 读取文件内容
                if data.get('md5'):  # 判断是否需要校验MD5
                    md5_obj = hashlib.md5()
                    for line in file_obj:
                        self.request.send(line)
                        md5_obj.update(line)
                    else:
                        file_obj.close()
                        md5_val = md5_obj.hexdigest()  # 获取md5值
                        self.send_response(258, {'md5': md5_val})  # 将MD5发送给客户端
                        print("send file done....")
                else:  # 不需要校验MD5，直接发送文件
                    for line in file_obj:
                        self.request.send(line)  # 按行发送文件
                    else:
                        file_obj.close()
                        print("send file done....")
        else:
            self.send_response(256)  # 如果文件不存在返回256

    def _put(self, *args, **kwargs):
        """接收客户端发送的文件"""
        data_dic = args[0]
        file_size = data_dic["size"]
        # 判断磁盘配额
        base_filename = data_dic["filename"].split('/')[-1]  # 如果输入的文件名是带有'/'的,取最后的文件名
        file_abs_path = "{}/{}".format(self.current_dir, base_filename)  # 获取当前文件路径

        if os.path.isfile(file_abs_path):  # 判断是否有同名文件
            self.send_response(261)
        else:
            self.send_response(200)
        with open(file_abs_path, "wb") as f:  # 打开一个空文件
            received_size = 0
            md5_obj = hashlib.md5()
            while received_size < file_size:  # 循环接收文件
                size = file_size - received_size
                if size < 4096:
                    data = self.request.recv(size)
                else:
                    data = self.request.recv(4096)
                md5_obj.update(data)  # 累加计算MD5
                f.write(data)  # 写入新文件
                received_size += len(data)  # 累加计算文件大小
            else:
                if data_dic.get('md5'):  # 判断是否需要校验MD5
                    md5_val = md5_obj.hexdigest()  # 计算出MD5值
                    md5_from_client = self.request.recv(1024)  # 接收客户端发送的MD5值
                    print(md5_val, md5_from_client)
                    if md5_from_client.decode() == md5_val:  # 与本地的MD5进行比较
                        print("文件校验成功！")
                print("file {} recv done...".format(base_filename))
            f.close()
