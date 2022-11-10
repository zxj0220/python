#!/usr/bin/python3
# !-*-coding:utf-8-*-
# __author__:"zxj"
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ftp_server这一层目录

USER_HOME = "{}/home" .format(BASE_DIR)  # 用户目录
LOG_DIR = "{}/log" .format(BASE_DIR)  # 日志目录
LOG_LEVEL = "DEBUG"  # 日志等级

ACCOUNT_FILE = "{}/conf/accounts.cfg" .format(BASE_DIR)  # 用户配置文件


HOST = "0.0.0.0"  # 服务器IP
PORT = 9999  # 程序端口
