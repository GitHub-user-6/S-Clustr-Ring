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
import socket
from Component.S_Clustr_AES import S_Clustr_AES_CBC
import os

info = '''
# ███████╗              ██╗  ██╗    ██╗  ██╗     ██████╗    ██╗  ██╗     ██╗    ██████╗
# ██╔════╝              ██║  ██║    ██║  ██║    ██╔════╝    ██║ ██╔╝    ███║    ╚════██╗
# ███████╗    █████╗    ███████║    ███████║    ██║         █████╔╝     ╚██║     █████╔╝
# ╚════██║    ╚════╝    ██╔══██║    ╚════██║    ██║         ██╔═██╗      ██║     ╚═══██╗
# ███████║              ██║  ██║         ██║    ╚██████╗    ██║  ██╗     ██║    ██████╔╝
# ╚══════╝              ╚═╝  ╚═╝         ╚═╝     ╚═════╝    ╚═╝  ╚═╝     ╚═╝    ╚═════╝
'''

def main():
    AESS = S_Clustr_AES_CBC()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER_ADDRESS = ('192.168.8.105', 10000)
    KEY = input("[KEY]>")
    client_socket.connect(SERVER_ADDRESS)
    data = AESS.aes_cbc_encode(KEY, '{"TYPE": "PC"}')
    client_socket.send(data.encode('utf-8'))
    while True:
        data=AESS.aes_cbc_decode(KEY,client_socket.recv(1024).decode('utf-8'))
        print("Recv:",data)
        if data=="RUN":
            print(info)
            # os.system("start http://www.bing.com")
            # print("Open Website...")
            # os.system("calc")
            # print("Open Calc...")
            client_socket.send("True".encode('utf-8'))
        elif data=="STOP":
            print("Exit")
            client_socket.send("False".encode('utf-8'))
            break
    client_socket.close()

if __name__ == '__main__':
    main()
