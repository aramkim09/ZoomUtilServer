#
# audio2captionServer.py
#



from socket import *
import time
import threading

# Imports the Google Cloud client library
from google.cloud import speech
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='/home/ubuntu/workspace/stt/stt_key/rock-idiom-279803-becd74ae58f1.json'

# Instantiates a client
client = speech.SpeechClient()

speech_context = speech.SpeechContext(phrases=["$TIME"]) # read file and add context

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=32000,
    language_code="ko-KR",
    speech_contexts=[speech_context],
)





try:
    # function for timer thread : every 5 sec send bytes to STT api
    def audio2caption():
        global datas
        time.sleep(8)
        while True:
            if(len(datas)<=0):
                time.sleep(5)
                continue
            else:

                lock = threading.Lock()
                lock.acquire()

                content=bytes(datas)
                #print("content",len(content))
                datas=bytearray()

                lock.release()
                audio = speech.RecognitionAudio(content=content)
                response = client.recognize(config=config, audio=audio)
                #print("im in")
                for result in response.results:
                    #print("im in2")
                    print("Transcript: {}".format(result.alternatives[0].transcript))


    def add_data(data):

        global datas
        lock = threading.Lock()
        lock.acquire()
        #print("data:",len(data))
        #print("datas",len(datas))
        datas=datas+data
        #print("datas",len(datas))

        lock.release()


    # function for syncronized adding client : add client information(number of id:connection socket object) to shared dictionary
    # by using lock, there is no concurrency issue.
    def add_client(id,ls,connect_sock):

        lock = threading.Lock()
        lock.acquire()

        ls[id]=connect_sock
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
    def client_thread(connectionSocket, clientAddress,id,counter_list):
        global datas

        add_client(id,counter_list,connectionSocket)

        while True:
            # receive binary data(ex-audio) from connected client
            data = connectionSocket.recv(4096)


            if data:
                #print(len(data))
                add_data(data)


            else:
                # if client socket close, then message received from connection socket is empty.
                # so exit while loop, and close connection socket
                break


        # if connection is closed, then delete client information in client dictionary and close connection socket.
        del_client(id,counter_list)
        connectionSocket.close()


    # make welcome socket
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSocket.bind(('', serverPort)) #serverSocket.bind(('ec2-52-79-239-124.ap-northeast-2.compute.amazonaws.com', serverPort))
    serverSocket.listen(1)
    print("The server is ready to receive on port", serverPort)

    # make client dictionary and id value for new client
    client_list={}
    id_counter=1
    global datas
    datas=bytearray()
    tt=threading.Thread(target= audio2caption,args=())
    tt.daemon=True
    tt.start()



    while True:

        # wait client connection.if connection request exist, make socket for client (=connection socket)
        (connectionSocket, clientAddress) = serverSocket.accept()

        # make thread and give socket and client ID
        t=threading.Thread(target=client_thread,args=(connectionSocket, clientAddress,id_counter,client_list))
        t.daemon=True
        t.start()
        id_counter+=1





except KeyboardInterrupt:
    # if there is KeyboardInterrupt, then close all socket and finish the program.
    for i in client_list:
        client_list[i].close()
    serverSocket.close()
    print("\nBye bye~")
