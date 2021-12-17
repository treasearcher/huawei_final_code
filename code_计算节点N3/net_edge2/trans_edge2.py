# -*- coding: utf-8 -*-
import logging
import threading
import queue
from socket import *
import numpy as np
import _thread
import time
import torch

qsize = 10
# ip_add = '127.0.0.1'
ip_add = '192.168.1.111'
server_port = 25002
connect_port = 25001

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def send_from(arr, dest):
    view = memoryview(arr).cast('B')
    while len(view):
        nsent = dest.send(view)
        view = view[nsent:]


def recv_into(arr, source):
    view = memoryview(arr).cast('B')
    while len(view):
        nrecv = source.recv_into(view)
        view = view[nrecv:]


def doConnect(host, port):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.settimeout(20)
    flag = True
    while flag:
        try:
            if flag:
                #log.info("try connect %s : %d", host, port)
                sock.connect((host, port))
                flag = False
               #log.info("try connect %s : %d SUCCESS", host, port)
        except Exception as e:
            pass
            #log.error("Address-related error connecting to server: %s" % e)
        time.sleep(3)
    return sock


class trans_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.d2Que = queue.Queue(qsize)
        self.d4Que = queue.Queue(qsize)
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind(('', server_port))
        self.server.listen(3)
        #log.info("bind %d", server_port)
        self.a_client, _ = self.server.accept()
        self.client = doConnect(ip_add, connect_port)
       # log.info('edge 2 init successfully')

    def get_d2(self):
        while self.d2Que.empty():
            #print('d2 is empty')
            time.sleep(0.1)
        self.lock.acquire()
        d2 = self.d2Que.get()
        self.lock.release()
        return d2

    def recv(self):
        try:
            arr = np.zeros(shape=(1, 128, 80, 80), dtype=np.float32)
            while 1:
                if not self.d2Que.full():
                    recv_into(arr, self.client)
                    d2 = torch.from_numpy(arr)
                    d2 = d2.cuda()
                    self.lock.acquire()
                    self.d2Que.put(d2)
                    self.lock.release()
                else:
                    # print('d2 is full')
                    time.sleep(0.1)
        except Exception as e:
            #log.error("connecting error: %s" % e)
            self.client = doConnect(ip_add, connect_port)

    def send(self):
        while 1:
            if not self.d4Que.empty():
                self.lock.acquire()
                d4 = self.d4Que.get()
                self.lock.release()
                d4 = d4.cpu().detach().numpy()
                send_from(d4, self.a_client)
            else:
                time.sleep(0.1)

    def put_d4(self, d4):
        while self.d4Que.full():
            # print('d2 is full')
            time.sleep(0.1)
        # d4 = d4.cpu().detach().numpy()
        self.lock.acquire()
        self.d4Que.put(d4)
        self.lock.release()

    def run(self):
        _thread.start_new_thread(self.recv, ())
        _thread.start_new_thread(self.send, ())

# def print_time(threadName, delay, counter):
#     while counter:
#         if exitFlag:
#             threadName.exit()
#         time.sleep(delay)
#         print ("%s: %s" % (threadName, time.ctime(time.time())))
#         counter -= 1
