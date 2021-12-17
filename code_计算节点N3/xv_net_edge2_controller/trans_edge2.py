import threading
import queue
from socket import *
import numpy as np
import _thread
import time
import torch


qsize=2
ip_add = '192.168.1.111'
#ip_add = '127.0.0.1'

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


class trans_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.d2Que = queue.Queue(qsize)
        self.boxQue = queue.Queue(qsize)
        self.client = socket(AF_INET, SOCK_STREAM)
        self.server = socket(AF_INET, SOCK_STREAM)
        self.client.connect((ip_add, 25001))
        self.server.bind(('', 25002))
        self.server.listen(1)
        self.a_client, _ = self.server.accept()
        print('edge 2 init successfully')

    def put_box(self, box):
        while self.boxQue.full():
            # print('box is full')
            time.sleep(0.1)
        self.lock.acquire()
        self.boxQue.put((len(box[0]), np.array(box, dtype=np.float32)))
        self.lock.release()

    def get_d2(self):
        while self.d2Que.empty():
            # print('d2 is empty')
            time.sleep(0.1)
        self.lock.acquire()
        d2 = self.d2Que.get()
        self.lock.release()
        return d2

    def recv(self):
        arr = np.zeros(shape=(1, 128, 80, 80), dtype=np.float32)
        while 1:
            if not self.d2Que.full():
                recv_into(arr, self.client)
                d2 = torch.from_numpy(arr)
                d2=d2.cuda()
                self.lock.acquire()
                self.d2Que.put(d2)
                self.lock.release()
            else:
                # print('d2 is full')
                time.sleep(0.1)

    def send(self):
        while 1:
            if not self.boxQue.empty():
                self.lock.acquire()
                lth, box=self.boxQue.get()
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
