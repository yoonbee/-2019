```python
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import audioop
import sys
import client
import MicrophoneStream as MS
import threading
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


KWSID = ['기가야', '지니야', '친구야', '자기야']

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
 
port = 8080

def thread1():
    while 1:
        call = test()
        while 1:
            if call:
                sentence = getVoice2Text()
                w.recvmsg.addItem(QListWidgetItem(sentence))
                w.c.send(sentence)
                break

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

def detect():
    with MS.MicrophoneStream(client.RATE, client.CHUNK) as stream:
        audio_generator = stream.generator()

        for content in audio_generator:
            rc = ktkws.detect(content)
            rms = audioop.rms(content, 2)
            if rc == 1:
                MS.play_file("../data/sample_sound.wav")
                return 200
            
def generate_request():
        with MS.MicrophoneStream(client.RATE, client.CHUNK) as stream:
            audio_generator = stream.generator()

            for content in audio_generator:
                message = gigagenieRPC_pb2.reqVoice()
                message.audioContent = content
                yield message
                
                rms = audioop.rms(content,2)
                #print_rms(rms)

def getVoice2Text():	
        print ("\n\n음성인식을 시작합니다.\n\n종료하시려면 Ctrl+\ 키를 누루세요.\n\n\n")
        channel = grpc.secure_channel('{}:{}'.format(client.HOST, client.PORT), UA.getCredentials())
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
    
class CWidget(QWidget):
                
    def __init__(self):
        super().__init__()  
         
        self.c = client.ClientSocket(self)
        
        self.initUI()
        
        input_thread = threading.Thread(target=thread1, args=())
        input_thread.start()
        
 
    def __del__(self):
        self.c.stop()
 
    def initUI(self):
        self.setWindowTitle('클라이언트')
         
        # 클라이언트 설정 부분
        ipbox = QHBoxLayout()
 
        gb = QGroupBox('서버 설정')
        ipbox.addWidget(gb)
 
        box = QHBoxLayout()
 
        label = QLabel('Server IP')
        self.ip = QLineEdit()
        self.ip.setInputMask('000.000.000.000;_')
        box.addWidget(label)
        box.addWidget(self.ip)
 
        label = QLabel('Server Port')
        self.port = QLineEdit(str(port))
        box.addWidget(label)
        box.addWidget(self.port)
 
        self.btn = QPushButton('접속')       
        self.btn.clicked.connect(self.connectClicked)
        box.addWidget(self.btn)
 
        gb.setLayout(box)       
 
        # 채팅창 부분  
        infobox = QHBoxLayout()      
        gb = QGroupBox('메시지')        
        infobox.addWidget(gb)
 
        box = QVBoxLayout()
         
        label = QLabel('받은 메시지')
        box.addWidget(label)
 
        self.recvmsg = QListWidget()
        box.addWidget(self.recvmsg)
 
        label = QLabel('보낼 메시지')
        box.addWidget(label)
 
        self.sendmsg = QTextEdit()
        self.sendmsg.setFixedHeight(50)
        box.addWidget(self.sendmsg)
 
        hbox = QHBoxLayout()
 
        box.addLayout(hbox)
        self.sendbtn = QPushButton('보내기')
        self.sendbtn.setAutoDefault(True)
        self.sendbtn.clicked.connect(self.sendMsg)
         
        self.clearbtn = QPushButton('채팅창 지움')
        self.clearbtn.clicked.connect(self.clearMsg)
 
        hbox.addWidget(self.sendbtn)
        hbox.addWidget(self.clearbtn)
        gb.setLayout(box)
 
        # 전체 배치
        vbox = QVBoxLayout()
        vbox.addLayout(ipbox)       
        vbox.addLayout(infobox)
        self.setLayout(vbox)
         
        self.show()
 
    def connectClicked(self):
        if self.c.bConnect == False:
            ip = self.ip.text()
            port = self.port.text()
            if self.c.connectServer(ip, int(port)):
                self.btn.setText('접속 종료')
                
            else:
                self.c.stop()
                self.sendmsg.clear()
                self.recvmsg.clear()
                self.btn.setText('접속')
        else:
            self.c.stop()
            self.sendmsg.clear()
            self.recvmsg.clear()
            self.btn.setText('접속')
 
    def updateMsg(self, msg):
        output_file = "testtts.wav"
        client.getText2VoiceStream(msg, output_file)
        MS.play_file(output_file)
        self.recvmsg.addItem(QListWidgetItem(msg))
 
    def updateDisconnect(self):
        self.btn.setText('접속')
        
    def sendMsg(self):
        sendmsg = self.sendmsg.toPlainText()
        self.recvmsg.addItem(QListWidgetItem(sendmsg))
        self.c.send(sendmsg)        
        self.sendmsg.clear()
 
    def clearMsg(self):
        self.recvmsg.clear()
 
    def closeEvent(self, e):
        self.c.stop()
     
    def detect():
        with MS.MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()

            for content in audio_generator:
                rc = ktkws.detect(content)
                rms = audioop.rms(content, 2)
                if rc == 1:
                    MS.play_file("../data/sample_sound.wav")
                    return 200

    
    def send(sock):
        while 1:
            call = test()
            while 1:
                if call:
                    sentence = getVoice2Text()
                    sock.send(sentence.encode())
                    break



 
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CWidget()
    sys.exit(app.exec_())
    sender = threading.Thread(target=send, args=(clientSocket,))
    sender.start()

    receiver = threading.Thread(target=receive, args=(clientSocket,))
    receiver.start()
  
```

