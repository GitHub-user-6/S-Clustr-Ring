#!/usr/bin/python3
# @Мартин.
# ███████╗              ██╗  ██╗    ██╗  ██╗     ██████╗    ██╗  ██╗     ██╗    ██████╗
# ██╔════╝              ██║  ██║    ██║  ██║    ██╔════╝    ██║ ██╔╝    ███║    ╚════██╗
# ███████╗    █████╗    ███████║    ███████║    ██║         █████╔╝     ╚██║     █████╔╝
# ╚════██║    ╚════╝    ██╔══██║    ╚════██║    ██║         ██╔═██╗      ██║     ╚═══██╗
# ███████║              ██║  ██║         ██║    ╚██████╗    ██║  ██╗     ██║    ██████╔╝
# ╚══════╝              ╚═╝  ╚═╝         ╚═╝     ╚═════╝    ╚═╝  ╚═╝     ╚═╝    ╚═════╝

import sys
sys.path.append(".")
from loguru import logger
import threading
import json
import socket
import string
import random
import hashlib
import re
import time
import argparse
import textwrap
from Component.S_Clustr_AES import S_Clustr_AES_CBC
from Component.DingTalkPush import DingTalk

configs = json.load(open('./Config/Version.conf'))[sys.argv[0].split('.')[0]]
title = f'''
************************************************************************************
<免责声明>:本工具仅供学习实验使用,请勿用于非法用途,否则自行承担相应的法律责任
<Disclaimer>:This tool is only for learning and experiment. Do not use it
for illegal purposes, or you will bear corresponding legal responsibilities
************************************************************************************
{configs['describe']}
'''
logo = f'''
███████╗       ██████╗██╗     ██╗   ██╗███████╗████████╗██████╗
██╔════╝      ██╔════╝██║     ██║   ██║██╔════╝╚══██╔══╝██╔══██╗
███████╗█████╗██║     ██║     ██║   ██║███████╗   ██║   ██████╔╝
╚════██║╚════╝██║     ██║     ██║   ██║╚════██║   ██║   ██╔══██╗
███████║      ╚██████╗███████╗╚██████╔╝███████║   ██║   ██║  ██║
╚══════╝       ╚═════╝╚══════╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝
                Github==>https://github.com/MartinxMax
                S-H4CK13@Мартин. S-Clustr(Shadow Cluster) Root Server {configs['version']}'''

def init_logger():
    logger.level(name="QUERY", no=38, color="<magenta>")
    logger.level(name="ROOT", no=40, color="<red>")
    logger.remove()
    logger.add(
        sink=sys.stdout,
        format="<green>[{time:HH:mm:ss}]</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
        colorize=True,
        backtrace=False,
        diagnose=False
    )
def myip():
    return socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)[0][4][0]

def generate_random_key(length=12):
    all_chars = string.ascii_letters + string.digits + string.punctuation
    random_chars = random.choices(all_chars, k=length)
    return ''.join(random_chars)


class s_h4ck13_s_clustr():
    def __init__(self,args):
        init_logger()
        self.__ROOT_DEVICES =dict()
        self.__s_h4ck13=S_Clustr_AES_CBC()

        if self.__check_parameters(args):
                if self.__reload_config():
                    self.__run()
                else:
                    logger.log("ROOT","[ERROR] Exception in path [./Config/Root.conf] configuration file, parameters may be incorrect")


    def __run(self):
        query_lock = threading.Lock()
        base_thread = threading.Thread(target=self.__s_clustr_server_root)
        base_thread.start()
        query_thread = threading.Thread(target=self.__s_clustr_root_query,args=(query_lock,))
        query_thread.start()

    def __is_valid_port(self, port):
        try:
            port = int(port)
            if 0 < port < 65536:
                return True
            else:
                return False
        except ValueError:
            return False
    def __check_parameters(self,args):
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', args.RIP):
            logger.log("ROOT"," [ERROR] Unreasonable host address!")
            return False
        if not self.__is_valid_port(args.RPO):
            logger.log("ROOT",f" [ERROR] Incorrect port! {args.RPO}")
            return False
        if not self.__is_valid_port(args.RQP):
            logger.log("ROOT",f" [ERROR] Incorrect port! {args.RQP}")
            return False
        if len(args.RK) < 6 or len(args.RQK)< 6:
            logger.log("ROOT",f" [ERROR] The key length must be greater than 6 !!!")
            return False
        self.__ROOT_PORT=args.RPO
        self.__ROOT_IP = args.RIP
        self.__ROOT_QUERY_PORT=args.RQP
        self.__ROOT_TOKEN = args.RK
        self.__ROOT_QUERY_TOKEN = args.RQK
        return True

    def __reload_config(self):
        try:
            self._Q_CONFIG = json.load(open('./Config/Root.conf'))
        except Exception as e:
            return False
        else:
            return True


    def __s_clustr_root_query(self,lock):
        q_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        q_socket.bind(('',self.__ROOT_QUERY_PORT))
        q_socket.listen(5)
        q_socket.settimeout(int(self._Q_CONFIG["QUERY_AUTH_TIMEOUT"]))
        logger.log("ROOT", f"[INFO] Root query service [{self.__ROOT_IP}:{self.__ROOT_QUERY_PORT}]")
        logger.log("ROOT", f"[INFO] Root query token [{hashlib.md5(self.__ROOT_QUERY_TOKEN.encode('utf-8')).hexdigest()}]")
        def device_info(ip,id):
            # if id == 0 and ip == '0.0.0.0': # {ip:{'ip':xxxx....}}
            #     ///////////////DEBUG///////////////
            #     result = dict()
            #     for ip_address, details in self.__ROOT_DEVICES.items():
            #             print("000>",ip_address)
            #             time.sleep(0.3)
            #             num_devices = details['device_max']
            #             ring_port = details['ring_port']
            #             device_port = details['device_port']

            #             result[ip_address] = {
            #                 'ring_port': ring_port,
            #                 'device_port': device_port,
            #                 'device_max': num_devices
            #             }
            #     return result
            if id == 0 and ip != '0.0.0.0':
                return self.__ROOT_DEVICES[ip]
            else:
                return {
                    'ip':ip,
                    'ring_port':self.__ROOT_DEVICES[ip]['ring_port'],
                    'device_port':self.__ROOT_DEVICES[ip]['device_port'],
                    'device_max':self.__ROOT_DEVICES[ip]['device_max'],
                    'device_type': self.__ROOT_DEVICES[ip]['device_type'].get(str(id), 'S-H4CK13'),
                    'device_state': self.__ROOT_DEVICES[ip]['device_state'].get(str(id), 'S-H4CK13'),
                    'device_connect_state': self.__ROOT_DEVICES[ip]['device_connect_state'].get(str(id), 'S-H4CK13'),
                    }

        def handle_client(client_socket, data,source_ip,lock):
            with lock:
                try:
                    data = json.loads(self.__s_h4ck13.aes_cbc_decode(self.__ROOT_QUERY_TOKEN,data))
                    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', data["target"]):
                        current_time = int(time.time())
                        ip = data["target"]
                        id = int(data["id"])
                        htimestamp = int(data["time"])
                        if current_time - htimestamp <= int(self._Q_CONFIG["QUERY_PACK_TIMEOUT"]):
                            if ip in self.__ROOT_DEVICES:
                                res = json.dumps(device_info(ip,id))
                                if res:
                                    res =self.__s_h4ck13.aes_cbc_encode(self.__ROOT_QUERY_TOKEN,res)
                                    client_socket.sendall(res.encode('utf-8'))
                                    logger.log("QUERY",f"[INFO] Forwarded information from [{ip}] device [{id}] to [{source_ip}]")
                                else:
                                    logger.log("QUERY",f"[ERROR] Problem with data parsing")

                        else:
                            logger.log("QUERY","[WARNING] Packet expired, suspected to be under replay attack")

                except Exception as e:
                    print(e)
                    logger.log("QUERY",f"[WARNING] The server received an abnormal packet from {source_ip}")
                finally:
                    client_socket.close()
        while True:
            try:
                client_socket, address = q_socket.accept()
                data = client_socket.recv(1024)
                client_thread = threading.Thread(target=handle_client, args=(client_socket, data.decode('utf-8'),address[0],lock))
                client_thread.start()
            except Exception as e:
                pass

    def __s_clustr_server_root(self):
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_socket.bind(('',self.__ROOT_PORT))
            logger.log("ROOT", f"[INFO] Root service [{self.__ROOT_IP}:{self.__ROOT_PORT}]")
            logger.log("ROOT", f"[INFO] Root token [{hashlib.md5(self.__ROOT_TOKEN.encode('utf-8')).hexdigest()}]")
            def handle_client(data:str, client_address:tuple):
                time.sleep(0.5)
                try:
                    device = json.loads(self.__s_h4ck13.aes_cbc_decode(self.__ROOT_TOKEN,data))
                except Exception as e:
                    return False
                else:
                    ip = device['ip']
                    if ip in self.__ROOT_DEVICES:
                        self.__ROOT_DEVICES[ip].update(device)
                    else:
                        self.__ROOT_DEVICES[ip] = device
            while True:
                data, client_address = server_socket.recvfrom(2048)
                client_thread = threading.Thread(target=handle_client, args=(data.decode('utf-8').strip(), client_address))
                client_thread.start()
                self.__reload_config()

if __name__ == '__main__':
    print(logo)
    print(title)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent('''
            Example:
                author-Github==>https://github.com/MartinxMax
            Basic usage:
                python3 {S_Clustr} -root-ip <STR> # Set local IP, automatically obtained by default
                python3 {S_Clustr} -root-port <INT> # Default 10090
                python3 {S_Clustr} -root-q-port <STR> # Default 10091
                python3 {S_Clustr} -root-key <STR> # Set the TOKEN of the root service to receive node data
                python3 {S_Clustr} -root-q-key <STR> # Set the TOKEN of the query service for anonymous users to query device status
                '''.format(S_Clustr=sys.argv[0],ip=myip())))
    parser.add_argument('-root-ip', '--RIP',default=myip(), help='Local server ip address')
    parser.add_argument('-root-port', '--RPO',type=int,default='10090', help='Local device connect port')
    parser.add_argument('-root-key', '--RK',default=generate_random_key(), help='Controlled device authentication key (Default random 6-digit password)')
    parser.add_argument('-root-q-key', '--RQK',default=generate_random_key(), help='Controlled device authentication key (Default random 6-digit password)')
    parser.add_argument('-root-q-port', '--RQP',type=int,default='10091', help='Local device connect port')
    args = parser.parse_args()
    s_h4ck13_s_clustr(args)
