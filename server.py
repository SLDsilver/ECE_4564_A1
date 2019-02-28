#!/usr/bin/env python3
import socket
import sys
import argparse as ap
import json
from cryptography.fernet import Fernet as fn
import hashlib
import pickle
import ServerKeys
import urllib.request
import os
import request_watson as watson



class Server:
    def __init__(self,host="",port=50000,backlog=5,size=1024,cp=False):
        self.cp = cp
        self.s = None
        self.client = None
        self.size=1024
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            self.s.bind((host,port))
            if self.cp: print("[Checkpoint 01] Created socket at ", self.s.getsockname()[0], " on port ", str(port))
            self.s.listen(backlog)
        except socket.error as message:
            if self.s:
                self.s.close()
            print ("Could not open socket: " + str(message))
            sys.exit(1)
        while 1: #constantly serve clients
            if self.cp: print("[Checkpoint 02] Listening for client connections")

            client,_ = self.s.accept()
            if self.cp: print("[Checkpoint 03] Accepted client connection from ", str(client.getsockname()[0]), " on port ",str(client.getsockname()[1]))

            msg, checksum = self.receive_msg(client)

            if checksum:
                self.speak_question(msg)
                answer = self.ask_wolphram(msg)
                self.send_msg(answer,client)
            else:
                print("Checksum Failed, Closing connection")

            client.close()

    def receive_msg(self, client):
        data = client.recv(self.size)
        if data:
            received = self.unpack_msg(pickle.loads(data))
            if received['checksum']:
                return (received['body'],True)
            else:
                return ("",False)

    def send_msg(self,msg,client):
        payload = pickle.dumps(self.pack_msg(msg))
        if self.cp: print("[Checkpoint 11] Sending Answer: ", payload)
        client.send(payload)


    def pack_msg(self,str):
        msg = dict()
        #Create and save encryption key
        key = fn.generate_key()
        encrypter = fn(key)
        msg['key'] = key.decode()
        msg['body'] = encrypter.encrypt(str.encode()).decode()
        if self.cp: print("[Checkpoint 09] Encrypt: Generated Key: ", msg['key'], " Cyper Text: ", msg['body'])

        msg['checksum'] = hashlib.md5(str.encode()).hexdigest()
        if self.cp: print("[Checkpoint 10] MD5 Checksum: ", msg['checksum'])
        return json.dumps(msg)

    def unpack_msg(self,str):
        if self.cp: print("[Checkpoint 04] Received Data: ", str)
        e_msg = json.loads(str)
        d_msg = dict()

        e_msg['key'] = e_msg['key'].encode()
        e_msg['body'] = e_msg['body'].encode()

        decrypter = fn(e_msg['key'])

        d_msg['body'] = decrypter.decrypt(e_msg['body']).decode()
        d_msg['checksum'] = e_msg['checksum'] == hashlib.md5(d_msg['body'].encode()).hexdigest()

        if self.cp: print("[Checkpoint 05] Decrypt: Key: ", e_msg['key'], " Plain text: ", d_msg['body'])

        return d_msg

    def speak_question(self, str):
        watson.request('question.wav',str)
        os.system('aplay question.wav')
        if self.cp: print("[Checkpoint 06] Speaking Question: ", str)
        return

    def ask_wolphram(self, str):
        if self.cp: print("[Checkpoint 07] Sending question to Wolphramalpha: ", str)
        url = "http://api.wolframalpha.com/v1/result?appid=" + ServerKeys.APP_ID + "&i=" + urllib.parse.quote_plus(str)
        ans = urllib.request.urlopen(url).read().decode()  
        if self.cp: print("[Checkpoint 08] Received answer from Wolframalpha: ", ans)
        return ans 

if __name__ == '__main__':
    #Add argument parser for user input arguments, with default values
    parser = ap.ArgumentParser(description="Launch the server module for Assignemnt 1")

    parser.add_argument('-sp',action='store',dest='port',type=int,help="Port to host server on, default 50000",default=50000,required=False)
    parser.add_argument('-z',action='store',dest='size',type=int,help="Socket size of the port, default 1024",default=1024,required=False)
    parser.add_argument('--silent',action='store_true',dest='silent',help="Disable checkopoint output, enabled by default",default=True,required=False)
    args = parser.parse_args()

    #start the server
    s = Server(port=args.port,size=args.size, cp=args.silent)
