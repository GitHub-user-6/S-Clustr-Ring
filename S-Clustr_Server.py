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
from cgitb import reset
from math import log
from loguru import logger
import time
import socket
import random
import string
import threading
import json
import re
import argparse
import textwrap
import hashlib
from Component.S_Clustr_AES import S_Clustr_AES_CBC
from Component.DingTalkPush import DingTalk
import copy

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
                S-H4CK13@Мартин. S-Clustr(Shadow Cluster) Server {configs['version']}'''
def init_logger():
    logger.level(name="Anonymous", no=38, color="<magenta>")
    logger.level(name="Device", no=39, color="<blue>")
    logger.level(name="System", no=40, color="<red>")
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




class Main():

    def __init__(self,args):
        init_logger()
        if not self.__reload_config():
            logger.log("System","Exception in path [./Config/] configuration file, parameters may be incorrect")
            return False
        elif self.__check_parameters(args):
            self.__aes=S_Clustr_AES_CBC()
            self.__DEVICE_IDS = {}
            self.__DEVICE_STATE = {}
            self.__DEVICE_CONNECT_STATE = {}
            self.__DEVICE_TYPE = {}
            for i in range(1, int(self._SER_CONFIG['MAX_DEV'])+1):
                self.__DEVICE_IDS[i] = None
                self.__DEVICE_TYPE[i] = None
                self.__DEVICE_STATE[i] = 0
                self.__DEVICE_CONNECT_STATE[i] = 0
                self.__BEHAVIORS = {1: 'RUN', 2: 'STOP', 3: 'Query State'}
            self.__run()
        else:return False


    def __run(self):
        device_thread = threading.Thread(target=self.__s_clustr_server_device)
        heartbeat_thread = threading.Thread(target=self.__s_clustr_send_heartbeat)
        core_thread = threading.Thread(target=self.__s_clustr_core)
        reload_config_thread = threading.Thread(target=self.__reload_config_roll)
        device_thread.start()
        logger.log("System", f" [INFO] Max devices [{self._SER_CONFIG['MAX_DEV']}]...")
        heartbeat_thread.start()
        logger.log("System",f" [INFO] Device heartbeat packet time [{self._SER_CONFIG['HEART']['TIMEOUT']}/s]")
        core_thread.start()
        reload_config_thread.start()
        logger.log("System", f" [CONFING] Configure file updates every {self._SER_CONFIG['CONFIG_UPDATE_TIME']} seconds")

# 程序参数检查
    def __check_parameters(self,args):
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', args.LI):
            logger.log("System"," [ERROR] Unreasonable host address!")
            return False
        if not self.__is_valid_port(args.SDP):
            logger.log("System"," [ERROR] Incorrect port!")
            return False
        if len(args.SK) < 6 or len(args.SDK) < 6 or len(args.RK) < 6:
            logger.log("System",f" [ERROR] The key length must be greater than 6 !!!")
            return False
        self.__local_ip = args.LI
        self.__server_dev_port = args.SDP
        self.__max_dev_num = int(self._SER_CONFIG['MAX_DEV'])
        self.__server_key = args.SK
        self.__server_dev_key = args.SDK
        self.__ring_key = args.RK
        self.__ring_port = args.RP
        if self._SER_CONFIG['DINGTALK']['TOKEN'] and self._SER_CONFIG['DINGTALK']['SECRET']:
            self.DINGTALK = DingTalk(False)
            self.DINGTALK.set_token(self._SER_CONFIG['DINGTALK']['TOKEN'])
            self.DINGTALK.set_secret(self._SER_CONFIG['DINGTALK']['SECRET'])
            logger.log("System",f" [INFO] DingTalk monitoring enabled")
            self.DINGTALK.send_text(logo)
        logger.log("System",f" [INFO] Server token [{hashlib.md5(self.__server_key.encode('utf-8')).hexdigest()}]")
        logger.log("System",f" [INFO] Device token [{hashlib.md5(self.__server_dev_key.encode('utf-8')).hexdigest()}]")
        logger.log("System",f" [INFO] Ring network token [{hashlib.md5(self.__ring_key.encode('utf-8')).hexdigest()}]")

        return True

# 配置文件重载
    def __reload_config(self):
        try:
            self._CLI_CONFIG = json.load(open('./Config/Client.conf'))
            self._SER_CONFIG = json.load(open('./Config/Server.conf'))
            self.__D_ROUTE_LIST = json.load(open('./Config/Proxy.conf'))["Route"]
            self.DEV_BLACKLIST = set(json.load(open('./Config/Blacklist.conf'))['Device']['BLACK-LIST'])
            # self.SER_BLACKLIST = set(json.load(open('./Config/Blacklist.conf'))['Anonymous']['BLACK-LIST'])
        except Exception as e:
            return False
        else:
            return True


    def __reload_config_roll(self):
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            self.__reload_config()
            if self._SER_CONFIG["REMOTE_ROOT_SERVER"]["TOKEN"] and \
                self._SER_CONFIG["REMOTE_ROOT_SERVER"]["IP"] and \
                self._SER_CONFIG["REMOTE_ROOT_SERVER"]["PORT"]:
                temp_socket.sendto(self.__aes.aes_cbc_encode(self._SER_CONFIG["REMOTE_ROOT_SERVER"]["TOKEN"],json.dumps(self.__get_devices_info())).encode('utf-8'),(self._SER_CONFIG["REMOTE_ROOT_SERVER"]["IP"],self._SER_CONFIG["REMOTE_ROOT_SERVER"]["PORT"]))
            time.sleep(self._SER_CONFIG["CONFIG_UPDATE_TIME"])

# 核心组件
    def __s_clustr_core(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('', self.__ring_port))
        logger.log("System",f" [INFO] Ring network service [{self.__local_ip}:{self.__ring_port}]")
        def analysis(data:str,server_token:str,ring_token:str=None):
            current_time = int(time.time())
            data_len = len(data)
            if data_len == 82:
                try:
                    raw_data = data.split('-')
                except Exception as e:
                    return False ,False,data_len
                else:
                    if len(raw_data) != 4: raise Exception
                    htimestamp = int(raw_data[0], 16)
                    device_id = int(raw_data[1], 16)
                    state = int(raw_data[2], 16)
                    sig = raw_data[3]
                    try:
                        result = int(self.__aes.aes_cbc_decode(server_token,sig))
                    except Exception as e:
                        return False,False,data_len
                    else:
                        if htimestamp == result and current_time - htimestamp <= int(self._SER_CONFIG['ANONYMOUS_PACK_TIMEOUT']):
                            return device_id,state,data_len
                        else:
                            return False,False,data_len
            elif data_len >= 384:
                try:
                    data=json.loads(self.__aes.aes_cbc_decode(ring_token,data))
                except Exception as e:
                    return False ,False,data_len
                else:
                    route_time = int(data["Time"])
                    raw_data = data["Data"].split('-')
                    if len(raw_data) != 4: raise Exception
                    htimestamp = int(raw_data[0], 16)
                    device_id = int(raw_data[1], 16)
                    state = int(raw_data[2], 16)
                    sig = raw_data[3]
                    try:
                        result = int(self.__aes.aes_cbc_decode(server_token,sig))
                    except Exception as e:
                        if self.__local_ip+':'+str(self.__ring_port) in data["Route"]:
                            logger.log("System",f" [WARNING] The packet did not find the correct destination and passed through the following route [{'->'.join(data['Route'])}]")
                            return False ,False,data_len
                        return "T",data,data_len
                    else:
                        if htimestamp == result and current_time - htimestamp <= int(self._SER_CONFIG['ANONYMOUS_PACK_TIMEOUT']):
                            if ring_token and data["Target"][0] in self.__local_ip+':'+str(self.__ring_port): # 判断是否为自己
                                logger.log("System",f" [ROUTE_TIME] The routing process takes {current_time - route_time} seconds to reach the server")
                                logger.log("System",f" [ROUTE_SERVER] From routes {data['Route']}")
                                logger.log("System",f" [ROUTE_HOPS] After {len(data['Route'])} hops, the server was reached")
                                logger.log("System",f" [ROUTE_DATA] Packet creation time before {current_time - htimestamp} second")
                                return device_id,state ,data_len
                        else:
                            return False ,False,data_len


        def transport_send(server_host:str, server_port:int, message:dict,client_address:tuple,ring_token:str):
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message_copy = copy.deepcopy(message)
            message_copy["Route"].append(self.__local_ip+':'+str(self.__ring_port))
            client_socket.sendto(self.__aes.aes_cbc_encode(key=ring_token,data=json.dumps(message_copy)).encode('utf-8'), (server_host, server_port))
            logger.log("System",f" [INFO] Forwarding packets from host {client_address[0]} to {server_host}:{server_port}, length: {len(message_copy['Data'])}")
            client_socket.close()


        def handle_client(data:str, client_address:tuple):
            time.sleep(0.5)
            try:
                id,stat,data_len =analysis(data=data,server_token=self.__server_key,ring_token=self.__ring_key)
            except Exception as e:
                print(e)
            else:
                if id == "T" and stat and data_len >= 384:
                    for route in self.__D_ROUTE_LIST:
                        transport_send(route.split(':')[0], int(route.split(':')[-1]), stat,client_address,self.__ring_key)
                elif id >=0  and stat and data_len:
                    source = "RING" if data_len >= 384 else "DIRECT"
                    if id == 0 and (stat == 1 or stat == 2):
                        device_ids_true_id = [key for key, value in self.__DEVICE_CONNECT_STATE.items() if value == 1]
                        if len(device_ids_true_id) > 0:
                            for id in device_ids_true_id:
                                try:
                                    if self.__check_devices(id,stat):
                                        self.__control_device(device_id=int(id),command=self._CLI_CONFIG[self.__DEVICE_TYPE[id]][ 'RUN' if stat == 1 else 'STOP'])
                                    else:
                                        logger.log("System", f" [WARNING] [{source}] Device offline, device [{id}] has been deleted")
                                except Exception as e:
                                    logger.log("Anonymous", f" [COMMAND] [{source}] Sending command {self.__BEHAVIORS[stat]} to device ID {id} failed!")
                        else:
                            logger.log("Anonymous", f" [COMMAND] [{source}] No devices are online!")
                    elif id >0 and (stat == 1 or stat == 2):
                        if self.__check_devices(id,stat):
                            self.__control_device(device_id=int(id), command=self._CLI_CONFIG[self.__DEVICE_TYPE[id]][ 'RUN' if stat == 1 else 'STOP'])
                            logger.log("Anonymous", f" [COMMAND] [{source}] Sending command {self.__BEHAVIORS[stat]} to device ID {id} successfully completed!")
                        else:
                            logger.log("Anonymous", f" [COMMAND] [{source}] [{id}] are offline!")

        while True:
            data, client_address = self.server_socket.recvfrom(1024)
            client_thread = threading.Thread(target=handle_client, args=(data.decode('utf-8').strip(), client_address))
            client_thread.start()



# 验证提供的数据是否为正确端口
    def __is_valid_port(self, port):
        try:
            port = int(port)
            if 0 < port < 65536:
                return True
            else:
                return False
        except ValueError:
            return False


    def __check_devices(self,id,stat):
        try:
            data = self._CLI_CONFIG[self.__DEVICE_TYPE[id]][ 'RUN' if stat == 1 else 'STOP']
        except Exception as e:
            return False
        else:
            return data
# 发送设备心跳包 检测在线情况
    def __s_clustr_send_heartbeat(self):
        while True:
            for dev_id in range(1, int(self._SER_CONFIG['MAX_DEV'])+1):
                client_socket = self.__DEVICE_IDS[dev_id]
                if client_socket:
                    try:
                        data=self._SER_CONFIG['HEART']['DATA']
                        if self._SER_CONFIG['DEV_ENCRYPTION_SERVER'][self.__DEVICE_TYPE[dev_id]]:
                            data = self.__aes.aes_cbc_encode(self.__server_dev_key,data)
                        client_socket.send(data.encode('utf-8'))
                    except Exception as e:
                        self.__device_disconnected(dev_id)
                        logger.log("System",f'[WARNIGN] Device ID {dev_id} dropped...')
                        if self._SER_CONFIG['DINGTALK']['TOKEN'] and self._SER_CONFIG['DINGTALK']['SECRET']:
                            self.DINGTALK.send_text(f"[WARNIGN] Device ID:[{dev_id}] dropped...")

            time.sleep(int(self._SER_CONFIG['HEART']['TIMEOUT']))

# 设备断开连接
    def __device_disconnected(self,device_id):
        self.__DEVICE_IDS[device_id] = None
        self.__DEVICE_CONNECT_STATE[device_id] = 0
        self.__DEVICE_STATE[device_id] = 0
        self.__DEVICE_TYPE[device_id] = None

# 查询设备控制状态
    def __get_devices_info(self):
        data = {
                'ip':self.__local_ip,
                'ring_port':self.__ring_port,
                'device_port':self.__server_dev_port,
                'device_max':self.__max_dev_num,
                'device_type':self.__DEVICE_TYPE,
                'device_state': self.__DEVICE_STATE,
                'device_connect_state': self.__DEVICE_CONNECT_STATE
                }

        return data

# 控制设备
    def __control_device(self,device_id=None, command=None):
        try:
            device_socket = self.__DEVICE_IDS[device_id]
            if device_socket:
                if self._SER_CONFIG['DEV_ENCRYPTION_SERVER'][self.__DEVICE_TYPE[device_id]] :
                        command = self.__aes.aes_cbc_encode(self.__server_dev_key,command)
                device_socket.send(command.encode('utf-8'))
                try:
                    respon = device_socket.recv(1024).decode('utf-8').strip()
                    if self._SER_CONFIG['DEV_ENCRYPTION_SERVER'][self.__DEVICE_TYPE[device_id]] :
                            respon = self.__aes.aes_cbc_decode(self.__server_dev_key,respon)
                except Exception as e:
                    return False
                else:
                    if respon:
                        if self._CLI_CONFIG[self.__DEVICE_TYPE[device_id]]['DEV_RUN_RECV'] == str(respon):
                            self.__DEVICE_STATE[device_id] = 1
                            logger.log("Device",f" [SUCCESS] Device:{str(device_id)} State:Runing...")
                            if self._SER_CONFIG['DINGTALK']['TOKEN'] and self._SER_CONFIG['DINGTALK']['SECRET']:
                                self.DINGTALK.send_text(f" [SUCCESS] Device:{str(device_id)} State:Runing...")

                        elif  self._CLI_CONFIG[self.__DEVICE_TYPE[device_id]]['DEV_STOP_RECV'] == respon:
                            self.__DEVICE_STATE[device_id] = 0
                            logger.log("Device",f" [SUCCESS] Device:{str(device_id)} State:Stoped...")
                            if self._SER_CONFIG['DINGTALK']['TOKEN'] and self._SER_CONFIG['DINGTALK']['SECRET']:
                                self.DINGTALK.send_text(f" [SUCCESS] Device:{str(device_id)} State:Stoped...")
                        else:
                            logger.log("Device",f" [Fail] Can't control Device:{str(device_id)}")
                    else:
                        return False
            else:
                return False
        except Exception as e:
            print(e)
            return False

# 设备主入口
    def __s_clustr_server_device(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', self.__server_dev_port))
        server_socket.listen(1)
        logger.log("System",f" [INFO] Device Service [{self.__local_ip}:{self.__server_dev_port}]")
        def assign_id(client_socket):
            for dev_id in range(1, self.__max_dev_num+1):
                if not self.__DEVICE_IDS[dev_id]:
                    self.__DEVICE_IDS[dev_id] = client_socket
                    self.__DEVICE_CONNECT_STATE[dev_id] = 1
                    return dev_id
            return None


        def is_json(str):
            try:
                json.loads(str)
                return True
            except ValueError:
                return False

        def handle_client(client_socket, client_address):
            if client_address[0] in self.DEV_BLACKLIST:
                logger.log("Device", f" [INFO] {client_address[0]} is on the blacklist")
                client_socket.close()
                return
            logger.log("Device", f" [INFO] {client_address[0]} connected")
            client_socket.settimeout(int(self._SER_CONFIG['DEV_AUTH_TIMEOUT']))
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not is_json(data):
                    data = self.__aes.aes_cbc_decode(self.__server_dev_key, data)
                data = json.loads(data)

                if data['TYPE'] not in self._SER_CONFIG['DEV_TYPE']:
                    raise ValueError(f"Invalid device type: {data['TYPE']}")
                device_id = assign_id(client_socket)
                if not device_id:
                    raise ValueError("Unable to assign ID to device")

                self.__DEVICE_TYPE[device_id] = data['TYPE']
                logger.log("Device", f" [INFO] Assigned ID[{str(device_id)}] to {client_address[0]} [Type:{self.__DEVICE_TYPE[device_id]}]")
                client_socket.settimeout(None)

                if self._SER_CONFIG['DINGTALK']['TOKEN'] and self._SER_CONFIG['DINGTALK']['SECRET']:
                    self.DINGTALK.send_text(f" [INFO] Device Assigned ID[{str(device_id)}] to {client_address[0]} [Type:{self.__DEVICE_TYPE[device_id]}]")

            except ValueError as e:
                logger.log("Device", f" [ERROR] {client_address[0]} failed validation: {str(e)}")
                client_socket.close()

            except Exception as e:
                logger.log("Device", f" [ERROR] {client_address[0]} failed validation: {str(e)}")
                client_socket.close()

        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()


if __name__ == '__main__':
    print(logo)
    print(title)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent('''
            Example:
                author-Github==>https://github.com/MartinxMax
            Basic usage:
                python3 {S_Clustr} -local-ip <STR> # Set local IP, automatically obtained by default
                python3 {S_Clustr} -server-dev-port <INT> # Default 10000
                python3 {S_Clustr} -ring-port <INT> # Default 10089
                python3 {S_Clustr} -server-key <STR> # Server key, with a length greater than or equal to 6 bits
                python3 {S_Clustr} -server-dev-key <STR> # Server key, with a length greater than or equal to 6 bits
                python3 {S_Clustr} -ring-key <STR> # Ring network access authentication key, length must be greater than or equal to 6 bits
                '''.format(S_Clustr=sys.argv[0],ip=myip())))
    parser.add_argument('-local-ip', '--LI',default=myip(), help='Local server ip address')
    parser.add_argument('-server-dev-port', '--SDP',type=int,default='10000', help='Local device connect port')
    parser.add_argument('-ring-port', '--RP',type=int,default='10089', help='Local ring network port')
    parser.add_argument('-server-key', '--SK',default=generate_random_key(), help='Server authentication key (Default random 6-digit password)')
    parser.add_argument('-server-dev-key', '--SDK',default=generate_random_key(), help='Controlled device authentication key (Default random 6-digit password)')
    parser.add_argument('-ring-key', '--RK',default=generate_random_key(), help='Ring network key (Default random 6-digit password)')
    args = parser.parse_args()
    Main(args)
