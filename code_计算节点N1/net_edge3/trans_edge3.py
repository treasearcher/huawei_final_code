# -*- coding: utf-8 -*-
import logging
import threading
import queue
from socket import *
import numpy as np
import _thread
import time
import torch
import cv2

qsize = 10
# ip_add = '127.0.0.1'
ip_add = '192.168.1.110'
server_port = 25003
connect_port = 25002

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
           # log.error("Address-related error connecting to server: %s" % e)
        time.sleep(3)
    return sock


class trans_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.d4Que = queue.Queue(qsize)
        self.boxQue = queue.Queue(qsize)
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind(('', 25003))
        self.server.listen(3)
        #log.info("bind %d", server_port)
        self.a_client, _ = self.server.accept()
        self.a_client.settimeout(5)
        self.client = doConnect(ip_add, connect_port)
        print('edge 3 init successfully')

    def put_box(self, box):
        while self.boxQue.full():
            # print('box is full')
            time.sleep(0.1)
        self.lock.acquire()
        self.boxQue.put((len(box[0]), np.array(box, dtype=np.float32)))
        self.lock.release()

    def get_d4(self):
        while self.d4Que.empty():
           # print('d4 is empty')
            time.sleep(0.1)
        self.lock.acquire()
        d4 = self.d4Que.get()
        self.lock.release()
        return d4

    def recv(self):
        arr = np.zeros(shape=(1, 256, 40, 40), dtype=np.float32)
        while 1:
            if not self.d4Que.full():
                recv_into(arr, self.client)
                d4 = torch.from_numpy(arr)
                d4 = d4.cuda()
                self.lock.acquire()
                self.d4Que.put(d4)
                self.lock.release()
            else:
                # print('d2 is full')
                time.sleep(0.1)

    def send(self):
        try:
            while 1:
                if not self.boxQue.empty():
                    self.lock.acquire()
                    lth, box = self.boxQue.get()
                    self.lock.release()
                    if lth == 0:
                        send_from(np.zeros(1, dtype=np.int64), self.a_client)
                    else:
                        lth = np.array([lth], dtype=np.int64)
                        send_from(lth, self.a_client)
                        send_from(box, self.a_client)
                else:
                    # print('box is empty')
                    time.sleep(0.1)
        except Exception as e:
            pass
            #log.error("connecting error: %s" % e)
            self.a_client, _ = self.server.accept()

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
