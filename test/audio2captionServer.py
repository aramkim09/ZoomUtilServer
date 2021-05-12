#
# audio2captionServer.py
#



from socket import *
import time
import threading
import client
import queue

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
        global datas
        time.sleep(8)
        while True:
            #time.sleep(5)
            if(datas.qsize()<=0):
                time.sleep(5)
                continue
            else:

                lock = threading.Lock()
                lock.acquire()

                item=datas.get()
                lock.release()

                content=bytes(item[1])
                #print("content",len(content))


                #print("id",id(datas))


                audio = speech.RecognitionAudio(content=content)
                response = stt_client.recognize(config=config, audio=audio)
                #print("im in")
                for result in response.results:
                    #print("im in2")
                    #print(type(result.alternatives[0].transcript))
                    print("{}: {}".format(item[0],result.alternatives[0].transcript))


    def add_data(data):

        global datas
        lock = threading.Lock()
        lock.acquire()
        #print("data:",len(data))
        #print("datas",len(datas))
        datas.put(data)
        #print("datas",len(datas))

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
        global datas

        id=c.getName()
        add_client(id,counter_list,c)
        timer=time.time()

        while True:
            # receive binary data(ex-audio) from connected client
            try:
                data = c.getSock().recv(4096)
            except Exception :
                break


            if data:
                #print(len(data))
                c.add(data)


            if(time.time()-timer>5):
                #add_data(c.getAll())
                datas.put((c.getName(),c.getAll()))
                timer=time.time()


        # if connection is closed, then delete client information in client dictionary and close connection socket.
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
    global datas # total audio queue
    datas=queue.Queue()
    tt=threading.Thread(target= audio2caption,args=())
    tt.daemon=True
    tt.start()



    while True:

        # wait client connection.if connection request exist, make socket for client (=connection socket)
        (connectionSocket, clientAddress) = serverSocket.accept()
        c=client.client()
        data = connectionSocket.recv(4096)
        if data:
            c.setName(data.decode())
        else:
            c.setName(id_counter)

        c.setSock(connectionSocket)
        c.setAddress(clientAddress)


        # make thread and give socket and client ID
        t=threading.Thread(target=client_thread,args=(client_list,c))
        t.daemon=True
        t.start()
        id_counter+=1





except KeyboardInterrupt:
    # if there is KeyboardInterrupt, then close all socket and finish the program.
    for i in client_list:
        client_list[i].getSock().close()
    serverSocket.close()
    print("\nBye bye~")
