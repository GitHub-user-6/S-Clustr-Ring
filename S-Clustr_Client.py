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
import cmd
import time
import socket
import json
from Component.S_Clustr_AES import S_Clustr_AES_CBC

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

class S_Clustr(cmd.Cmd):
    intro = 'Welcome to S-Clustr console. Type [options][help/?] to list commands.\n'
    prompt = f'[S-H4CK13@S-Clustr]<{configs["version"]}># '


    def __init__(self):
        super().__init__()
        self.PAYLOAD = PAYLOAD()
        self.options = {
            "s-key": {"value":"","description":"Server token (TOKEN)(UDP)(Ring network)"},
            "s-host": {"value":"","description":"Server ip (UDP)(Ring network)"},
            "s-port": {"value":"10089","description":"Server port (UDP)(Ring network)"},
            "id": {"value":"","description":"Device ID [0-n/0 represents specifying all]"},
            "pwr": {"value":"","description":"Device behavior (run[1]/stop[2]/Query device status[3])(1/2-UDP(Ring network))(3-TCP)"},

            "rnt-host": {"value":"","description":"Proxy server (UDP)(Ring network)"},
            "rnt-port": {"value":"10089","description":"Proxy server port(UDP)(Ring network)"},
            "rnt-key": {"value":"","description":"Ring token (TOKEN)(UDP)(Ring network)"},

            "root-q-host": {"value":"","description":"Root server ip (QUERY)(TCP)(ROOT)"},
            "root-q-port": {"value":"10091","description":"Root server port (QUERY)(TCP)(ROOT)"},
            "root-q-key": {"value":"","description":"Root server token (TOKEN)(QUERY)(TCP)(ROOT)"},

        }


    def do_set(self, arg):
        """Set an option value. Usage: set <option> <value>"""
        try:
            option, value = arg.split()
        except ValueError:
            print("[-] Invalid syntax. Usage: set <option> <value>")
            return
        else:
            if option in self.options:
                if value.lower() == 'none':
                    value=None
                self.options[option]['value'] = value
                print(f'[*] {option} => {value}')
            else:
                print(f'[-] Unknown variable: {option}')


    def do_run(self,arg):
        print("[*] Connecting to the server...")
        self.PAYLOAD.run(self.options)


    def do_options(self, arg):
        """List all available options and their current values."""
        table =  "| Name           | Current Setting | Required | Description       \n"
        table += "|:--------------:|:---------------:|:--------:|:-----------------\n"
        for key in self.options:
            name = f"{key:<14}"
            setting = f"{self.options[key]['value'] if self.options[key]['value'] else ' ':<15}"
            required = f"{'no' if self.options[key]['value'] else 'yes':<8}"
            description = f"{self.options[key]['description']:<20}"
            table += f"| {name} | {setting} | {required} | {description}\n"
        table += "|:--------------:|:---------------:|:--------:|:-----------------\n"
        print(table)


    def do_exit(self, arg):
        """Exit the program. Usage: exit"""
        return True


class PAYLOAD():

    def analysis(self,data:str,server_token:str,ring_token:str=None):
            try:
                if ring_token:
                    data=json.loads(self.__aes.aes_cbc_decode(ring_token,data))
                    raw_data = data["Data"].split('-')
                    route_time = int(data["Time"])
                else:
                    raw_data = data.strip().split('-')
                if len(raw_data) != 4: raise Exception
                current_time = int(time.time())
                htimestamp = int(raw_data[0], 16)
                device_id = int(raw_data[1], 16)
                state = int(raw_data[2], 16)
                sig = raw_data[3]
                result = int(self.__aes.aes_cbc_decode(key=server_token,data=sig))
                route_time=current_time
                if htimestamp == result and current_time - htimestamp <= int(30):
                    return current_time - route_time ,current_time - htimestamp,device_id,state
                raise Exception
            except Exception as e:
                print(e)
                return False


    def build_payload(self,rhost:str,rport:int,id:int,stat:int,server_token:str,thost:str=None, tport:int=None,ring_token:str=None):
            try:
                currentTime = int(time.time())
                signature = self.__aes.aes_cbc_encode(server_token, str(currentTime))
                payload = self.__build_data_payload(currentTime,id,stat,signature)
                if thost and tport and ring_token and server_token and rhost and rport:
                    target_str = f"{rhost}:{rport}"
                    jsons = {
                        "Time": currentTime,
                        "Route": [],
                        "Target": [target_str],
                        "Data": payload
                    }
                    return self.__aes.aes_cbc_encode(ring_token, json.dumps(jsons))
                elif rhost and rport and server_token:
                    return payload
                else:
                    return False
            except Exception as e:
                print(e)
                return False


    # def __analysis(self,data:str,server_token:str,ring_token:str=None):
    #     current_time = int(time.time())
    #     print(ring_token)
    #     print(data)
    #     print(self.__aes.aes_cbc_decode(key=ring_token,data=data))


    def __init__(self):
        self.__aes=S_Clustr_AES_CBC()
        self.__BEHAVIORS = {1: 'RUN', 2: 'STOP', 3: 'Query State'}


    def run(self,info):
        if self.__check_params_complete(info):
            id = int(info['id']['value'])
            pwr = int(info['pwr']['value'])

            server_token = info['s-key']['value']
            server_ip = info['s-host']['value']
            server_port = int(info['s-port']['value'])

            Ring_target_tserver_ip = info['rnt-host']['value']
            Ring_target_tserver_port = int(info['rnt-port']['value'])
            Ring_token = info['rnt-key']['value']

            root_server_ip = info['root-q-host']['value']
            root_port = int(info['root-q-port']['value'])
            root_query_token = info['root-q-key']['value']

            if pwr >0 and pwr < 3 and server_ip and server_port and server_token:
                if Ring_target_tserver_ip and Ring_target_tserver_port and Ring_token:
                    data=self.build_payload(
                        server_token=server_token,
                        id=id,
                        stat=pwr,
                        thost=Ring_target_tserver_ip,
                        tport=Ring_target_tserver_port,
                        rhost=server_ip,
                        rport=server_port,
                        ring_token=Ring_token
                                            )
                    self.__udp_transport(
                        ip=Ring_target_tserver_ip,
                        port=Ring_target_tserver_port,
                        data=data,
                        )
                else:
                    data=self.build_payload(
                        server_token=server_token,
                        id=id,
                        stat=pwr,
                        rhost=server_ip,
                        rport=server_port)
                    self.__udp_transport(
                        ip=server_ip,
                        port=server_port,
                        data=data,
                        )
            elif pwr ==3 :
                data=self.__query_build_payload(
                        token=root_query_token,
                        id=id,
                        rhost=server_ip
                        )
                self.__query(
                    ip=root_server_ip,
                    port=root_port,
                    data = data,
                    token = root_query_token,
                    r_host=server_ip,
                    id=id
                )

    def __check_params_complete(self,info):
        for key in ['id', 'pwr']:
            if key not in info or not info[key].get('value'):
                print(f"[-] Parameter '{key}' is missing or incomplete!")
                return False
        return True


    def __query_build_payload(self,rhost:str,id:int,token:str):
        currentTime = int(time.time())
        jsona = {
            'target':rhost,
            'id':id,
            'time':currentTime
        }
        return self.__aes.aes_cbc_encode(token,json.dumps(jsona))


    def __query(self, ip: str, port: int, data: str, token: str, r_host: str, id:int):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, port))
            client.send(data.encode('utf-8'))
            response = client.recv(2048).decode('utf-8')
            if response:
                json_response = json.loads(self.__aes.aes_cbc_decode(token, response))
                if id == 0:
                        if r_host != '0.0.0.0':
                            self.__display(json_response,id)
                else:
                    self.__display(json_response,id)
            client.close()
        except socket.timeout as e:
            print(e)
            print(f"The is not online")
        except Exception as e:
            print(e)
            print(f"The server under the root [{ip}] is not online")
            if client:
                client.close()


    def __udp_transport(self, ip:str,port:int,data:str):
        response=''
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data.encode('utf-8'), (ip, int(port)))
        print(f"[*] Sending to [{ip}:{port}]")
        client_socket.close()
        return response

    def __build_data_payload(self,time,id,state,signature):
        return f"{time:08x}-{id:05x}-{state:02x}-{signature}"

    def __display(self, json_response, id):
        print("IP      | Ring Port | Device Port | Device_max | ID | Type  | Status  | Network")
        print("-" * 76)
        if id==0:
            for index in range(1, len(json_response['device_type']) + 1):
                str_index = str(index)
                device_type = json_response['device_type'].get(str_index, 'None') if isinstance(json_response['device_type'], dict) else 'None'
                device_state = json_response['device_state'].get(str_index, False) if isinstance(json_response['device_state'], dict) else False
                device_connect_state = json_response['device_connect_state'].get(str_index, False) if isinstance(json_response['device_connect_state'], dict) else False
                print(f"{json_response['ip']} | {json_response['ring_port']}     | {json_response['device_port']}       | {json_response['device_max']}        | {str_index} | {device_type} | {'Running' if device_state else 'Stopped'} | {'Connected' if device_connect_state else 'Disconnected'}")
        else:
            print(f"{json_response['ip']} | {json_response['ring_port']}     | {json_response['device_port']}       | {json_response['device_max']}        | {id} | {json_response['device_type']} | {'Running' if json_response['device_state'] else 'Stopped'} | {'Connected' if json_response['device_connect_state'] else 'Disconnected'}")


if __name__ == '__main__':
    print(logo)
    print(title)
    S_Clustr().cmdloop()
