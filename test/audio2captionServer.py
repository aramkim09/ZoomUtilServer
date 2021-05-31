#
# audio2captionServer.py
#



from socket import *
import time
import threading
import client
import queue
import json
# for making STT dataset
import makeSttDataset as msd

# Imports the Google Cloud client library
from google.cloud import speech
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='/home/ubuntu/workspace/stt/stt_key/rock-idiom-279803-becd74ae58f1.json'

# Instantiates a client
stt_client = speech.SpeechClient()
global speech_context
speech_context = speech.SpeechContext(phrases=[]) # read file and add context
global config
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=32000,
    language_code="ko-KR",
    #speech_contexts=[speech_context],
)





try:

    def makeDataset(filename):

        global stt_context
        global config

        msd.make_dataset(filename)
        with open('/home/ubuntu/workspace/demo/json/PDFPPT_dataset.json',encoding="utf8") as json_file:
            json_data=json.load(json_file)
            json_context=json_data['speechContexts']
            json_phrase=json_context[0]['phrases']
        speech_context = speech.SpeechContext(phrases=json_phrase)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=32000,
            language_code="ko-KR",
            speech_contexts=[speech_context],
        )

    def sub_STT(sttQ):
        global config
        buffer=None#for test
        time.sleep(5)
        while True:
            if(sttQ.qsize()>0):
                stt_item=sttQ.get()
                #if buffer!=None:
                #content=bytes(buffer[2][:]+stt_item[2][:])
                #else:
                content=bytes(stt_item[2][:])

                #buffer=stt_item
                #bytequeue.clear()
                #print("content",len(content))
                if not content:
                    continue

                #print(len(content))

                audio = speech.RecognitionAudio(content=content)
                response = stt_client.recognize(config=config, audio=audio)
                send_name=stt_item[1][:]
                send_time=stt_item[0][:]
                #name=""
                #timestamp=""

                #print("im in")
                for result in response.results:
                    #print("im in2")
                    #print(type(result.alternatives[0].transcript))
                    if not result.alternatives[0].transcript:
                        continue
                    print("[{}] {}: {}".format(send_time,send_name,result.alternatives[0].transcript))
                    talkQ.put((send_time,send_name,result.alternatives[0].transcript))
            else:
                time.sleep(1)

    def timer(sttQ,user_audio,name):
        user_name=name
        lock = threading.Lock()
        while True:
            time.sleep(3)
            lock.acquire()
            if user_audio[user_name]!=None:
                sttQ.put(user_audio[user_name])
                user_audio[user_name]=None
            lock.release()

    # function for STT thread : every 5 sec send bytes to STT api
    def audioProcessing():

        #print("STT Thread")
        global dataQ
        global talkQ
        lock = threading.Lock()
        #buffer=None #buffer for dataQ
        #bytequeue=bytearray()
        #name=""
        #timestamp=""
        sttQ=queue.PriorityQueue()
        user_audio={}
        user_time={}

        t=threading.Thread(target=sub_STT,args=(sttQ,))
        t.daemon=True
        t.start()
        time.sleep(2)
        start=time.time()

        ### sholud make each timeout for each client

        while True:
            #time.sleep(5)
            if(dataQ.qsize()>0):
                item=dataQ.get() # item[0]=time item[1]=name item[2]=data
                if item[1] in user_audio:
                    if(user_audio[item[1]]==None):
                        lock.acquire()
                        user_audio[item[1]]=list(item)
                        lock.release()
                        user_time[item[1]]=time.time()
                    else:
                        lock.acquire()
                        user_audio[item[1]][2]=user_audio[item[1]][2]+item[2]
                        lock.release()
                        #if(len(user_audio[item[1]][2])>250000):#if(time.time()-user_time[item[1]]>3):#if(len(user_audio[item[1]][2])>200000):
                            #sttQ.put(user_audio[item[1]])
                            #user_audio[item[1]]=None
                            #user_time[item[1]]=time.time()
                        #lock.release()

                else:
                    user_audio[item[1]]=list(item)
                    user_time[item[1]]=time.time()
                    t=threading.Thread(target=timer,args=(sttQ,user_audio,item[1]))
                    t.daemon=True
                    t.start()
                #if(time.time()-start>1):
                    #for i in user_time:
                        #if(time.time()-user_time[i]>3):
                            #sttQ.put(user_audio[item[1]])
                            #user_audio[item[1]]=None
                            #user_time[i]=time.time()
                    #start=time.time()

            else:
                time.sleep(1)






    # function for sending and saving transcript to dbQ thread
    def caption2client(client_list):

        #print("Caption 2 client Thread")
        global talkQ
        global dbQ
        lock = threading.Lock()
        type=0

        time.sleep(8)
        while True:
            time.sleep(1)
            if(talkQ.qsize()<=0):
                time.sleep(1)
                continue
            else:


                lock.acquire()

                item=talkQ.get()
                lock.release()

                lock.acquire()
                dbQ.put(item)
                lock.release()

                # item = (timestamp,username,transcript)
                a=(item[1]+":"+item[2]).encode()+bytes(1)
                length=int.to_bytes(len(a), 4,byteorder="big")
                data=bytes([type])+length+item[0].encode()+bytes(1)+a
                # data = type+datasize+timestamp(+bytes)+data(username+":"+transcript+bytes)
                # make subthread sending data to all client
                t=threading.Thread(target=send_all,args=(client_list,data))
                t.daemon=True
                t.start()



    def send_all(client_list,data):

        for i in client_list:
            try:
                client_list[i].getSock().send(data)
            except Exception:
                continue




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


    # function for host thread : communicate with host
    def client_thread(counter_list,c):
        global dataQ
        global sessionName
        #f=open("zoom.raw","wb")
        id=c.getName()
        add_client(id,counter_list,c)
        timer=time.time()
        file_name=""
        file_data=bytearray()
        stop=False # for flag
        file_size=0
        send_counter=1
        while True:
            # receive binary data(ex-audio) from connected client
            try:
                data = c.getSock().recv(3000000)
            except Exception :
                break
            if(data):
                #print(len(data))

                while(True):
                    data_type=data[0]
                    #if(data_type!=6):
                    data_size=int.from_bytes(data[1:5], "big")


                    if(data_type==0):
                        # type = set sesssionName
                        pass
                        #sessionName=data[5:data_size+5].decode()
                        #if(len(data)>data_size+5):
                        #    data=data[data_size+5:]
                        #else:
                        #    break
                    elif(data_type==1):
                        # type = set sessionType
                        break #pass
                    elif(data_type==2):
                        if(len(data)<6):

                            break
                        # type = set userName
                        try:
                            c.setName(data[5:data_size+5].decode())
                            #print("name byte")
                            #for i in data[5:data_size+5]:
                                #print(hex(i)," ",i)

                        except:
                            print("[Error]")
                            print("type:",data_type)
                            print("total size:",len(data))
                            print("data_size:",data_size)
                            break
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
                        if(len(data)<18):
                            break

                        # type = audioRawdata
                        #print("data_type:",data_type)
                        #print("data_size:",data_size)
                        #print("total_size",len(data))
                        try:
                            timestamp=data[5:13].decode()
                        except:
                            print("[Error]")
                            print("type:",data_type)
                            print("total size:",len(data))
                            print("data_size:",data_size)
                            break

                        user_name_size=int.from_bytes(data[13:17], "big")
                        #print("user_name_size",user_name_size)
                        try:
                            user_name=data[17:17+user_name_size].decode()
                            #int.from_bytes(data[17:17+user_name_size], "little")
                            #print("name byte")
                            #for i in data[17:17+user_name_size]:
                                #print(hex(i)," ",i)
                            #print("user_name:",user_name)
                        except:
                            print("[Error]")
                            print("type:",data_type)
                            print("total size:",len(data))
                            print("data_size:",data_size)
                            print("name_size",user_name_size)
                            #int.from_bytes(data[17:17+user_name_size], "little"

                            break
                        dataQ.put((timestamp,user_name,data[17+user_name_size:data_size+17+user_name_size]))
                        #c.add(timestamp,data[17+user_name_size:data_size+17+user_name_size])
                        if(len(data)>data_size+17+user_name_size):
                            data=data[data_size+17+user_name_size:]
                        else:
                            break
                        #print(timestamp)
                    elif(data_type==5):
                        # type = fileName
                        #filename=""
                        if(stop):
                            if(len(data)>data_size+9):
                                data=data[data_size+9:]
                                continue
                            else:
                                break
                        if(len(data)<6):

                            break
                        try:
                            file_size=int.from_bytes(data[5:9], "big")
                            file_name=data[9:data_size+9].decode() # ppt or pdf
                            print("file_size",file_size)
                            print(file_name)
                            #for i in data[5:data_size+5]:
                                #print(hex(i)," ",i)
                            path='/home/ubuntu/workspace/demo/data/'
                            f=open(path+file_name,"wb")

                        except:
                            print("[Error]")
                            print("type:",data_type)
                            print("total size:",len(data))
                            print("data_size:",data_size)
                            break
                        if(len(data)>data_size+9):
                            data=data[data_size+9:]
                        else:
                            break


                    elif(data_type==6):
                        # type = fileData
                        if(stop):
                            break
                        if(len(data)<2):

                            break

                        note=data[5:5+data_size]
                        if note:
                            #print(len(file_data))
                            file_data=file_data+note
                            #1print(send_counter,"writing data sizeof",len(note),"| Total data size :",len(file_data))
                            send_counter+=1
                            if(len(file_data)>=file_size):
                                print("finish downloading file")
                                f.write(bytes(file_data))
                                f.close()
                                makeDataset(file_name)
                                stop=True
                                c.getSock().send("fin".encode())
                        if(len(data)>data_size+5):
                            data=data[data_size+5:]
                        else:
                            break

                        #pass
                    elif(data_type==7):
                        # type = manual correct Request
                        break #pass
                    else:
                        # cannot decode data, so discard
                        break
                    #print(len(data))


            """
            if(time.time()-timer>5):
                #pass
                temp=c.getAll()
                #f.write(bytes(temp)) #for test
                dataQ.put((c.getTime(),c.getName(),temp))
                c.resetTime()
                timer=time.time()"""


        # if connection is closed, then delete client information in client dictionary and close connection socket.
        #f=open("zoom.raw","wb")
        #f.write(bytes(c.getAll()))
        #f.close()
        print("connection closing",id)
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
    dataQ=queue.Queue()#queue.PriorityQueue()#queue.Queue()
    global talkQ
    talkQ=queue.Queue()
    global dbQ
    dbQ=queue.Queue()
    global sessionName
    sessionName=""
    thread_list=[]
    tt=threading.Thread(target= audioProcessing,args=())
    tt.daemon=True
    tt.start()

    t=threading.Thread(target=caption2client,args=(client_list,))
    t.daemon=True
    t.start()



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

    print("\nall transcript")
    while(talkQ.qsize()>0):
        i=talkQ.get()
        print("[",i[0],"]",i[1],":",i[2])
    for i in client_list:
        client_list[i].getSock().close()
    serverSocket.close()
    print("\nBye bye~")
