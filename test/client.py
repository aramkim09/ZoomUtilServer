# define client class
#import threading


class client:

    def __init__(self):
        self.bytequeue=bytearray()
        self.name=""
        self.sock=""
        self.address=""
        self.timestamp=""

    def __init__(self,input_name,input_sock,input_addr):
        self.bytequeue=bytearray()
        self.name=input_name
        self.sock=input_sock
        self.address=input_addr
        self.timestamp=""

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

    def getTime(self):
        return self.timestamp

    def resetTime(self):
        self.timestamp=""

    def add(self,time,data):
        # data format should be tuple (string->timestamp,bytes->audioRawdata)
        if(self.timestamp==""):
            self.timestamp=time
        self.bytequeue=self.bytequeue+data

    def getAll(self):
        return_value=self.bytequeue[:]
        self.bytequeue.clear()
        return return_value
