```
from __future__ import print_function

import threading
import time

import audioop
from ctypes import *
import ktkws # KWS

import grpc
import gigagenieRPC_pb2
import gigagenieRPC_pb2_grpc
import MicrophoneStream as MS
import user_auth as UA
import os
from ctypes import *

from socket import *

from threading import *
from socket import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
 
  

HOST = 'gate.gigagenie.ai'
PORT = 4080
RATE = 16000
CHUNK = 512
KWSID = ['기가지니', '지니야', '친구야', '자기야']


class Signal(QObject):  
    recv_signal = pyqtSignal(str)
    disconn_signal = pyqtSignal()   
 
class ClientSocket:
 
    def __init__(self, parent):        
        self.parent = parent                
        
        self.recv = Signal()        
        self.recv.recv_signal.connect(self.parent.updateMsg)
        self.disconn = Signal()        
        self.disconn.disconn_signal.connect(self.parent.updateDisconnect)
 
        self.bConnect = False
         
    def __del__(self):
        self.stop()
 
    def connectServer(self, ip, port):
        self.client = socket(AF_INET, SOCK_STREAM)           
 
        try:
            self.client.connect( (ip, port) )
        except Exception as e:
            print('Connect Error : ', e)
            return False
        else:
            self.bConnect = True
            self.t = Thread(target=self.receive, args=(self.client,))
            self.t.start()
            print('Connected')
 
        return True
 
    def stop(self):
        self.bConnect = False       
        if hasattr(self, 'client'):            
            self.client.close()
            del(self.client)
            print('Client Stop') 
            self.disconn.disconn_signal.emit()


    def receive(self, client):
        while self.bConnect:            
            try:
                recv = client.recv(1024)                
            except Exception as e:
                print('Recv() Error :', e)                
                break
            else:                
                msg = str(recv, encoding='utf-8')
                if msg:
                    self.recv.recv_signal.emit(msg)
                    print('[RECV]:', msg)
 
        self.stop()
    
         
    def send(self, msg):
         
            if not self.bConnect:
                return
 
            try:            
                self.client.send(msg.encode())
            except Exception as e:
                print('Send() Error : ', e)
            
       
            
'''
def sends(sock):
        while 1:
            call = test()
            while 1:
                if call:
                    sentence = getVoice2Text()
                    sock.send(sentence.encode())
                    break
'''
     
     
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
        
def py_error_handler(filename, line, function, err, fmt):
    dummy_var = 0
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)


def detect():
    with MS.MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()

        for content in audio_generator:
            rc = ktkws.detect(content)
            rms = audioop.rms(content, 2)
            if rc == 1:
                MS.play_file("../data/sample_sound.wav")
                return 200


def test(key_word='지니야'):
    rc = ktkws.init("../data/kwsmodel.pack")
    print('init rc = %d' % rc)
    rc = ktkws.start()
    print('start rc = %d' % rc)
    print('\n호출어를 불러보세요~\n')
    ktkws.set_keyword(KWSID.index(key_word))
    rc = detect()
    print(rc)
    print('\n\n호출어가 정상적으로 인식되었습니다.\n\n')
    ktkws.stop()
    return rc


def generate_request():
    with MS.MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()

        for content in audio_generator:
            message = gigagenieRPC_pb2.reqVoice()
            message.audioContent = content
            yield message
            
            rms = audioop.rms(content,2)
            #print_rms(rms)

# STT
def getVoice2Text():	
    print ("\n\n음성인식을 시작합니다.\n\n종료하시려면 Ctrl+\ 키를 누루세요.\n\n\n")
    channel = grpc.secure_channel('{}:{}'.format(HOST, PORT), UA.getCredentials())
    stub = gigagenieRPC_pb2_grpc.GigagenieStub(channel)
    request = generate_request()
    resultText = ''
    for response in stub.getVoice2Text(request):
        if response.resultCd == 200: # partial
        # print('resultCd=%d | recognizedText= %s' 
              # % (response.resultCd, response.recognizedText))
            resultText = response.recognizedText
        elif response.resultCd == 201: # final
        # print('resultCd=%d | recognizedText= %s' 
              # % (response.resultCd, response.recognizedText))
            resultText = response.recognizedText
            break
        else:
        # print('resultCd=%d | recognizedText= %s' 
              # % (response.resultCd, response.recognizedText))
            break

    print ("\n\n인식결과: %s \n\n\n" % (resultText))
    return resultText


# TTS : getText2VoiceStream
def getText2VoiceStream(inText,inFileName):

        channel = grpc.secure_channel('{}:{}'.format(HOST, PORT), UA.getCredentials())
        stub = gigagenieRPC_pb2_grpc.GigagenieStub(channel)

        message = gigagenieRPC_pb2.reqText()
        message.lang=0
        message.mode=0
        message.text=inText
        writeFile=open(inFileName,'wb')
        for response in stub.getText2VoiceStream(message):
            if response.HasField("resOptions"):
                print ("\n\nResVoiceResult: %d" %(response.resOptions.resultCd))
            if response.HasField("audioContent"):
                print ("Audio Stream\n\n")
                writeFile.write(response.audioContent)
        writeFile.close()
        return response.resOptions.resultCd
    

def sends(sock):
    while 1:
        call = test()
        while 1:
            if call:
                sentence = getVoice2Text()
                sock.send(sentence.encode())
                break


def receives(sock):
    while 1:
        sentence = sock.recv(1024)
        output_file = "testtts.wav"
        getText2VoiceStream(sentence, output_file)
        MS.play_file(output_file)
        print( output_file + "이 생성되었으니 파일을 확인바랍니다. \n\n\n")
        print("상대방: " + sentence.decode('utf-8'))


            
    
```

