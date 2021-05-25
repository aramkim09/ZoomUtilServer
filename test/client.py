# define client class
#import threading
import threading

class client:

    def __init__(self):
        self.bytequeue=bytearray()
        self.name=""
        self.sock=""
        self.address=""
        self.timestamp=""
        self.lock = threading.Lock()


    def __init__(self,input_name,input_sock,input_addr):
        self.bytequeue=bytearray()
        self.name=input_name
        self.sock=input_sock
        self.address=input_addr
        self.timestamp=""
        self.lock = threading.Lock()

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
        self.lock.acquire()
        self.bytequeue=self.bytequeue+data
        self.lock.release()

    def getAll(self):
        self.lock.acquire()
        return_value=self.bytequeue[:]
        self.bytequeue.clear()
        self.lock.release()
        return return_value
