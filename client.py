#!/usr/bin/env python3
import socket
import sys
import argparse as ap
import json
from cryptography.fernet import Fernet as fn
import hashlib
import pickle
from imutils.video import VideoStream
from pyzbar import pyzbar
import time
import cv2
import ServerKeys
import os

class Client:
    def __init__(self,host='localhost',port=50000,size=1024,msg='Hello, world',cp=False):
        self.cp = cp
        self.s = None
        self.size=size
        try:
            if self.cp: print("[Checkpoint 01] Connecting to ", str(host), " on port ", str(port))
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((host,port))
        
        except socket.error as message:
            if self.s:
                self.s.close()
            print ("Unable to open the socket: " + str(message))
            sys.exit(1)
        
        question = self.readQR()
        self.send_msg(question)
        msg, checksum = self.receive_msg(self.s)
        if checksum:
            self.speak_answer(msg)
        else:
            print("Checksum Failed, Closing connection")
        
        self.s.close()
    
    def speak_answer(self,str):
        command = 'curl -X POST -u "apikey:' + ServerKeys.WATSON_KEY + '" --header "Content-Type: application/json" --header "Accept: audio/wav" --data \'{"text": "' + str + '"}\' --output out.wav "https://gateway-wdc.watsonplatform.net/text-to-speech/api/v1/synthesize"'
        os.system(command)
        os.system('aplay out.wav')
        if self.cp: print("[Checkpoint 08] Speaking answer: ",str)
        return
    
    def receive_msg(self, client):
        data = client.recv(self.size)
        if data:
            received = self.unpack_msg(pickle.loads(data))
            if received['checksum']:
                return (received['body'],True)
            else:
                return ("",False)

    def send_msg(self,msg):
        payload = pickle.dumps(self.pack_msg(msg))
        if self.cp: print("[Checkpoint 05] Sending Data: ", payload)
        self.s.send(payload)
    
    def readQR(self):
        # Starts Camera
        #print("Starting video")
        vs = VideoStream(usePiCamera=True).start()
        time.sleep(2.0)

        # Variable that tells whether a barcode was found
        found = 0 
        barcodeData = ""

        # Loop to find a QR code
        while (found == 0):
            
            #Reads a frame of the video
            frame = vs.read()

            #Stores barcodes in a variable
            barcodes = pyzbar.decode(frame)

            # Loop through barcodes (if more than one in frame)
            for barcode in barcodes:
                barcodeData = barcode.data.decode("utf-8")
                print(barcodeData)
                found = 1;

            # Outputs video
            cv2.imshow("Barcode Scanner", frame)
            cv2.waitKey(1)

        # Complete and Close
        #print("Complete")
        cv2.destroyAllWindows()
        vs.stop()

        if self.cp: print("[Checkpoint 02] Listening for QR codes from RPi Camera that contain questions")
        if self.cp: print("[Checkpoint 03] New Question: ", barcodeData)
        return barcodeData
    
    def pack_msg(self,str):
        msg = dict()
        #Create and save encryption key
        key = fn.generate_key()
        encrypter = fn(key)
        msg['key'] = key.decode()
        msg['body'] = encrypter.encrypt(str.encode()).decode()
        if self.cp: print("[Checkpoint 04] Encrypt: Generated Key: ", msg['key'], " Cyper Text: ", msg['body'])
        
        msg['checksum'] = hashlib.md5(str.encode()).hexdigest()
        
        return json.dumps(msg)
    
    def unpack_msg(self,str):
        if self.cp: print("[Checkpoint 06] Received Data: ", str)
        e_msg = json.loads(str)
        d_msg = dict()
        
        e_msg['key'] = e_msg['key'].encode()
        e_msg['body'] = e_msg['body'].encode()
        
        decrypter = fn(e_msg['key'])
        
        d_msg['body'] = decrypter.decrypt(e_msg['body']).decode()
        d_msg['checksum'] = e_msg['checksum'] == hashlib.md5(d_msg['body'].encode()).hexdigest()
        
        if self.cp: print("[Checkpoint 07] Decrypt: Key: ", e_msg['key'], " Plain text: ", d_msg['body'])
        
        return d_msg

if __name__ == '__main__':
    parser = ap.ArgumentParser(description="Launch the server module for Assignemnt 1")
    
    parser.add_argument('-sip',action='store',dest='IP',type=str,nargs='+',help="IP server is hosted on, default localhost",default='localhost',required=False)
    parser.add_argument('-sp',action='store',dest='port',type=int,help="Port request server on, default 50000",default=50000,required=False)
    parser.add_argument('-z',action='store',dest='size',type=int,help="Socket size of the port, default 1024",default=1024,required=False)
    parser.add_argument('--silent',action='store_true',dest='silent',help="Disable checkopoint output, enabled by default",default=True,required=False)
    
    args = parser.parse_args()
    client = Client(host=args.IP,port=args.port,size=args.size, cp=args.silent)
