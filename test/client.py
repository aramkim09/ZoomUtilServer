# define client class
#import threading


class client:

    def __init__(self):
        self.bytequeue=bytearray()
        self.name=""
        self.sock=""
        self.address=""

    def __init__(self,input_name,input_sock,input_addr):
        self.bytequeue=bytearray()
        self.name=input_name
        self.sock=input_sock
        self.address=input_addr

    def setAddress(self,input):
        self.address=input

    def getAddress(self,input):
        return self.address

    def setName(self,input):
        self.name=input

    def getName(self):
        return self.name

    def setSock(self,input):
        self.sock=input

    def getSock(self):
        return self.sock

    def add(self,data):
        # data format should be tuple (string->timestamp,bytes->audioRawdata)
        self.bytequeue=self.bytequeue+data

    def getAll(self):
        return_value=self.bytequeue[:]
        self.bytequeue.clear()
        return return_value
