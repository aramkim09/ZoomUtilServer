#
# audio2captionServer.py
#



from socket import *
import time
import threading
import client


# Imports the Google Cloud client library
from google.cloud import speech
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='/home/ubuntu/workspace/stt/stt_key/rock-idiom-279803-becd74ae58f1.json'

# Instantiates a client
stt_client = speech.SpeechClient()

speech_context = speech.SpeechContext(phrases=["$TIME"]) # read file and add context

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=32000,
    language_code="ko-KR",
    speech_contexts=[speech_context],
)





try:
    # function for STT thread : every 5 sec send bytes to STT api
    def audio2caption():
        global dataQ
        global talkQ
        time.sleep(8)
        while True:
            #time.sleep(5)
            if(dataQ.qsize()<=0):
                time.sleep(5)
                continue
            else:

                lock = threading.Lock()
                lock.acquire()

                item=dataQ.get()
                lock.release()

                content=bytes(item[2])
                #print("content",len(content))


                #print("id",id(dataQ))


                audio = speech.RecognitionAudio(content=content)
                response = stt_client.recognize(config=config, audio=audio)
                #print("im in")
                for result in response.results:
                    #print("im in2")
                    #print(type(result.alternatives[0].transcript))
                    print("[{}] {}: {}".format(item[0],item[1],result.alternatives[0].transcript))
                    talkQ.put((item[0],item[1],result.alternatives[0].transcript))

    # function for sending and saving transcript thread : every 5 sec send transcript to client
    def caption2client():
        global talkQ
        time.sleep(8)
        while True:
            time.sleep(2)
            if(talkQ.qsize()<=0):
                time.sleep(5)
                continue
            else:

                lock = threading.Lock()
                lock.acquire()

                item=talkQ.get()
                lock.release()

                # item = (timestamp,username,transcript)
                length=int.to_bytes(len(item[1]+":"+item[2]), 4,byteorder="big")
                data=bytes([type])+length+item[0].encode()+(item[1]+":"+item[2]).encode()
                # data = type+datasize+timestamp+data(username+":"+transcript)
                try:
                    connectionSocket.send(data)
                except Exception:
                    break





    def add_data(data):

        global dataQ
        lock = threading.Lock()
        lock.acquire()
        #print("data:",len(data))
        #print("dataQ",len(dataQ))
        dataQ.put(data)
        #print("dataQ",len(dataQ))

        lock.release()


    # function for syncronized adding client : add client information(number of id:connection socket object) to shared dictionary
    # by using lock, there is no concurrency issue.
    def add_client(id,ls,c):

        lock = threading.Lock()
        lock.acquire()

        ls[id]=c
        print( "Client {0} connected. Number of connected clients = {1}".format(id,len(ls)))

        lock.release()

    # function for syncronized deleting client : delete client information(number of id:connection socket object) in shared dictionary
    # by using lock, there is no concurrency issue.
    def del_client(id,ls):

        lock = threading.Lock()
        lock.acquire()

        del ls[id]
        print( "Client {0} disconnected. Number of connected clients = {1}".format(id,len(ls)))

        lock.release()


    # function for each client thread : communicate with each client
    def client_thread(counter_list,c):
        global dataQ
        global sessionName
        #f=open("zoom.raw","wb")
        id=c.getName()
        add_client(id,counter_list,c)
        timer=time.time()

        while True:
            # receive binary data(ex-audio) from connected client
            try:
                data = c.getSock().recv(4096)
            except Exception :
                break
            if(data):
                #print(len(data))
                while(True):
                    data_type=data[0]
                    data_size=int.from_bytes(data[1:5], "big")

                    if(data_type==0):
                        # type = set sesssionName
                        sessionName=data[5:data_size+5].decode()
                        if(len(data)>data_size+5):
                            data=data[data_size+5:]
                        else:
                            break
                    elif(data_type==1):
                        # type = set sessionType
                        break #pass
                    elif(data_type==2):
                        # type = set userName
                        c.setName(data[5:data_size+5].decode())
                        del_client(id,counter_list)
                        id=c.getName()
                        add_client(id,counter_list,c)
                        if(len(data)>data_size+5):
                            data=data[data_size+5:]
                        else:
                            break
                    elif(data_type==3):
                        # type = text
                        break #pass
                    elif(data_type==4):
                        # type = audioRawdata
                        #print("data_type:",data_type)
                        #print("data_size:",data_size)
                        #print("total_size",len(data))
                        timestamp=data[5:13].decode()
                        c.add(timestamp,data[13:data_size+13])
                        if(len(data)>data_size+13):
                            data=data[data_size+13:]
                        else:
                            break
                        #print(timestamp)
                    elif(data_type==5):
                        # type = fileName
                        break #pass
                    elif(data_type==6):
                        # type = fileData
                        break #pass
                    elif(data_type==7):
                        # type = manual correct Request
                        break #pass
                    else:
                        # cannot decode data, so discard
                        break
                    #print(len(data))



            if(time.time()-timer>5):
                #pass
                temp=c.getAll()
                #f.write(bytes(temp)) #for test
                dataQ.put((c.getTime(),c.getName(),temp))
                c.resetTime()
                timer=time.time()


        # if connection is closed, then delete client information in client dictionary and close connection socket.
        #f=open("zoom.raw","wb")
        #f.write(bytes(c.getAll()))
        #f.close()
        del_client(id,counter_list)
        c.getSock().close()
        del c


    # make welcome socket
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSocket.bind(('', serverPort))
    serverSocket.listen(1)
    print("The server is ready to receive on port", serverPort)

    # make client dictionary and id value for new client
    client_list={} # client dictinoray is comprised of userID:clientObject
    id_counter=1
    global dataQ # total audio queue
    dataQ=queue.Queue()
    global talkQ
    talkQ=queue.Queue()
    global sessionName
    sessionName=""
    thread_list=[]
    tt=threading.Thread(target= audio2caption,args=())
    tt.daemon=True
    tt.start()



    while True:

        # wait client connection.if connection request exist, make socket for client (=connection socket)
        (connectionSocket, clientAddress) = serverSocket.accept()
        c=client.client(id_counter,connectionSocket,clientAddress)

        # make thread and give socket and client ID
        t=threading.Thread(target=client_thread,args=(client_list,c))
        t.daemon=True
        t.start()
        #thread_list.append(t)
        id_counter+=1





except KeyboardInterrupt:
    # if there is KeyboardInterrupt, then close all socket and finish the program.
    # soon add stopping all sub thread

    print("all transcript")
    while(talkQ.qsize()>0):
        i=talkQ.get()
        print("[",i[0],"]",i[1],":",i[2])
    for i in client_list:
        client_list[i].getSock().close()
    serverSocket.close()
    print("\nBye bye~")
