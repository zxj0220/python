#!/usr/bin/python3
#!_*_coding:utf-8_*_
# __author__:"zxj"

import optparse
from core.ftp_server import FTPHandler
import socketserver
from conf import settings


class ArgvHandler(object):
    def __init__(self):
        self.parser = optparse.OptionParser()  # 在命令行添加选项
        # parser.add_option("-s","--host",dest="host",help="server binding host address")  # 配置ip
        # parser.add_option("-p","--port",dest="port",help="server binding port")  # 配置端口
        (options, args) = self.parser.parse_args()  # 调用parse_args()返回一个字典和列表
        self.verify_args(options, args)

    def verify_args(self,options,args):
        '''校验并调用相应的功能'''
        if args:
            if hasattr(self,args[0]):
                func = getattr(self,args[0])
                func()
            else:
                exit("usage:start/stop")

        else:
            exit("usage:start/stop")

    def start(self):
        print('---\033[32;1mStarting FTP server on {}:{}\033[0m----' .format(settings.HOST, settings.PORT))
        # 创建FTP服务器
        server = socketserver.ThreadingTCPServer((settings.HOST, settings.PORT), FTPHandler)
        # 激活服务器；这会一直持续到使用Ctrl-C中断程序
        server.serve_forever()

    def stop(self):
        pass




