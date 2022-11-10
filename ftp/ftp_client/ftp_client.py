#!/usr/bin/python3
# !_*_coding:utf-8_*_
# __author__:"zxj"
import readline  # 解决Linux系统中无法使用退格键的问题
import socket
import os
import json
import hashlib
import optparse
import getpass
import sys

STATUS_CODE = {  # 状态码
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",  # 无效的命令格式
    251: "Invalid cmd ",  # 无效命令
    252: "Invalid auth data",  # 身份验证数据无效
    253: "Wrong username or password!",  # 用户名或密码错误
    254: "Passed authentication!",  # 通过认证
}


class FtpClient(object):
    """
    FTP客户端类，处理客户端的所有操作
    """

    def __init__(self):
        self.user = None

        parser = optparse.OptionParser()  # 在命令行添加选项
        parser.add_option("-s", "--server_host", dest="server", help="ftp server ip_addr")  # ip
        parser.add_option("-P", "--port", type="int", dest="port", help="ftp server port")  # 端口
        parser.add_option("-u", "--username", dest="username", help="username")  # 用户名
        parser.add_option("-p", "--password", dest="password", help="password")  # 密码
        self.options, self.args = parser.parse_args()
        '''
        调用parse_args()返回一个字典和列表
        字典是dest中设定好的 eg：server：127.0.0.1
        列表是后续新添加的
        '''
        self.verify_args(self.options, self.args)  # 校验参数合法型
        self.connect()

    def connect(self):
        # 连接函数,与服务器端建立连接
        self.client = socket.socket()
        self.client.connect((self.options.server, self.options.port))

    def verify_args(self, options, args):
        """校验参数合法型"""

        if options.username is not None and options.password is not None:  # 用户和密码，两个都不为空
            pass
        elif options.username is None and options.password is None:  # 用户和密码，两个都为空
            pass
        else:
            # options.username is None or options.password is None:
            exit("Err: username and password must be provided together..")  # 必须同时提供用户名和密码

        if options.server and options.port:
            # print(options)
            if 0 < options.port < 65535:
                return True
            else:
                exit("Err:host port must in 0-65535")
        else:
            exit("Error:must supply ftp server address, use -h to check all available arguments.")

    def authenticate(self):
        """用户验证"""
        if self.options.username:
            print(self.options.username, self.options.password)
            return self.get_auth_result(self.options.username, self.options.password)
            # 当获取到一个用户名时，执行get_auth_result，获取函数返回的结果,如果为Ture，说明验证成功
        else:
            # 匿名用户**
            pass

    def get_auth_result(self, user, password):
        """获取用户身份验证结果"""
        data = {'action': 'auth',
                'username': user,
                'password': password}
        self.client.send(json.dumps(data).encode())  # 将用户身份信息发送到服务器端验证，实际应该加密发送**
        response = self.get_response()  # 调用get_response获取服务器端回复的结果

        if response.get('status_code') == 254:  # 如果服务器端回复的状态码为254，说明验证通过了
            print(STATUS_CODE[254])  # 输出254状态码对应的描述
            self.user = user
            return True
        else:
            print(response.get("status_msg"))

    def get_response(self):
        """接收服务器端返回的数据"""
        data = self.client.recv(1024)
        # print("server res", data)
        data = json.loads(data.decode())
        return data

    def interactive(self):
        # 交互式函数，与用户交互
        if self.authenticate():  # 调用用户验证函数通过后才执行后续代码
            print("---start interactive with u...")
            self.terminal_display = "[{}]$:".format(self.user)  # 在终端显示用户名
            while True:  # 死循环，直到用户退出程序
                cmd = input(self.terminal_display).strip()  # 用户输入命令
                if len(cmd) == 0:
                    continue  # 如果命令为空，则跳出当前循环，重新输入
                cmd_list = cmd.split()  # 获取命令,以空格切片
                if hasattr(self, "_{}".format(cmd_list[0])):  # 判断命令对应的函数是否存在
                    func = getattr(self, "_{}".format(cmd_list[0]))  # 存在的话获取函数的内存地址
                    func(cmd_list)  # 调用函数，将命令列表传入函数中
                else:
                    print("Invalid cmd,type 'help' to check available commands. ")

    def __md5_required(self, cmd_list):
        """检测命令是否需要进行MD5验证"""
        if '--md5' in cmd_list:
            return True

    def _help(self, *args, **kwargs):
        # 帮助函数
        supported_actions = """
        get filename    #get file from FTP server
        put filename    #upload file to FTP server
        ls              #list files in current dir on FTP server
        pwd             #check current path on server
        cd path         #change directory , same usage as linux cd command
        exit            #exit this program
        """
        print(supported_actions)

    def show_progress(self, total):
        """显示进度条**"""
        received_size = 0  # 当前文件大小
        current_percent = 0  # 当前百分比进度
        while received_size < total:  # 如果当前文件大小 小于 文件总大小，继续循环
            if int((received_size / total) * 100) > current_percent:  # 如果当前文件大小/文件总大小 大于 当前百分比进度
                print("#", end="", flush=True)  # 输出#号，flush=Ture：立即刷新
                current_percent = int((received_size / total) * 100)
            new_size = yield  # 将函数定义为生成器，在此处中断
            received_size += new_size

    def _cd(self, *args, **kwargs):
        """切换目录"""
        # print("cd args", args)
        if len(args[0]) > 1:  # 判断cd命令是否带了目录
            path = args[0][1]
        else:
            path = ''
        data = {'action': 'change_dir', 'path': path}
        self.client.send(json.dumps(data).encode())  # 将要切换的目录发送给服务器
        response = self.get_response()  # 接收服务器返回的结果
        if response.get("status_code") == 260:  # 260表示目录切换成功
            self.terminal_display = "{}:".format(response.get('data').get("current_path"))  # 在终端显示当前路径
        else:
            print(response.get("status_code"), response.get("status_msg"))  # 路径不存在，输出错误

    def _pwd(self, *args, **kwargs):
        """查看当前目录"""
        data = {'action': 'pwd'}
        self.client.send(json.dumps(data).encode())  # 发送pwd命令给服务器
        response = self.get_response()  # 接收服务器返回的结果
        if response.get("status_code") == 200:
            data = response.get('data')
            print(data)

    def _ls(self, *args, **kwargs):
        if len(args[0]) > 1:  # 判断ls命令是否带了目录
            path = args[0][1]
        else:
            path = ''
        data = {'action': 'listdir', 'path': path}

        self.client.send(json.dumps(data).encode())  # 发送ls命令和目录给服务器
        response = self.get_response()  # 接收服务器返回的结果
        if response.get("status_code") == 200:
            data = response.get('data')
            print(data[1])

    def _put(self, *args):
        """上传文件"""
        if len(args[0]) == 1:  # 命令长度为1，缺少文件名，退出函数
            print("no filename follows...")
            return
        data = args[0]
        filename = data[1]  # 获取文件名
        if os.path.isfile(filename):  # 判断文件是否存在
            file_size = os.stat(filename).st_size  # 获取文件大小
            data_header = {
                "action": 'put',
                "filename": filename,
                "size": file_size
            }
            if self.__md5_required(args[0]):
                data_header['md5'] = True
            self.client.send(json.dumps(data_header).encode("utf-8"))  # 将文件名和文件大小发送给服务器
            server_response = self.client.recv(1024)  # 防止粘包，等服务器确认
            print(server_response.decode())
            with open(filename, "rb") as file_obj:  # 读取文件内容
                if self.__md5_required(args[0]):
                    md5_obj = hashlib.md5()
                    for line in file_obj:
                        self.client.send(line)  # 按行传输文件
                        md5_obj.update(line)  # 累加MD5
                    else:
                        file_obj.close()
                        md5_val = md5_obj.hexdigest().encode()
                        print("file md5", md5_val)
                        self.client.send(md5_val)  # 将MD5发送给服务器
                        print("文件上传成功！")
                else:  # 不需要验证MD5
                    for line in file_obj:
                        self.client.send(line)  # 按行传输文件
                    else:
                        file_obj.close()
                        print("文件上传成功！")
        else:
            print(filename, "文件不存在")

    def _get(self, *args):
        """从服务器上下载文件"""
        print("get--", args[0])
        if len(args[0]) == 1:  # 命令长度为1，缺少文件名，退出函数
            print("no filename follows...")
            return
        data_header = {
            'action': 'get',
            'filename': args[0][1]  # 文件名/文件路径+文件名
        }
        if self.__md5_required(args[0]):
            data_header['md5'] = True  # 如果需要对文件进行md5验证，在data_header中加一个字段
            print(data_header)

        self.client.send(json.dumps(data_header).encode())  # 发送data_header给服务器
        response = self.get_response()  # 接收服务器返回的文件大小
        print(response)
        file_total_size = response['data']['file_size']  # 获取文件总大小
        if response["status_code"] == 257:  # 服务器准备发送文件
            self.client.send(b'1')  # 防止粘包，客户端确认接收文件
            base_filename = args[0][1].split('/')[-1]  # 如果输入的文件名是带有'/'的,取最后的文件名
            received_size = 0  # 已接收的文件大小

            with open(base_filename, "wb") as file_obj:  # 打开一个空文件
                if file_total_size == 0:  # 如果文件为空文件，退出函数
                    file_obj.close()
                    return
                progress = self.show_progress(file_total_size)  # 显示进度条
                progress.__next__()
                md5_obj = hashlib.md5()
                while received_size < file_total_size:  # 循环接收文件
                    size = file_total_size - received_size
                    if size < 4096:
                        data = self.client.recv(size)  # 防止粘包，最后一次接收文件可能小于4096
                    else:
                        data = self.client.recv(4096)  # 每次接收4096字节的文件内容

                    received_size += len(data)  # 文件大小累加
                    try:
                        progress.send(len(data))  # 迭代显示进度条
                    except StopIteration as e:  # 捕获异常
                        print("100%")
                    file_obj.write(data)
                    md5_obj.update(data)
                else:
                    print("----->文件下载完成----")
                    file_obj.close()
                    if self.__md5_required(args[0]):  # 如果需要对文件进行MD5验证
                        md5_val = md5_obj.hexdigest()  # 获取总的MD5值
                        md5_from_server = self.get_response()  # 获取服务器上文件的MD5值
                        if md5_from_server['data']['md5'] == md5_val:  # 与本地的MD5进行比较
                            print("%s 文件一致性校验成功!" % base_filename)
                        # print(md5_val, md5_from_server)


if __name__ == "__main__":
    ftp = FtpClient()  # 实例化
    ftp.interactive()  # 交互
