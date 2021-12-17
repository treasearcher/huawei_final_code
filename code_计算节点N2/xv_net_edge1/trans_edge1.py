import threading
import queue
from socket import *
import numpy as np
import _thread
import time
import cv2
import torch


qsize=10
ip_add = '192.168.1.103'
#ip_add = '192.168.1.104'
#ip_add = '127.0.0.1'


height = 320
width = 320

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
        self.imgQue = queue.Queue(qsize)
        self.d2Que = queue.Queue(qsize)
        self.client = socket(AF_INET, SOCK_STREAM)
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind(('', 25001))
        self.server.listen(1)
        print('edge 1 success 1')
        self.a_clinet, _ = self.server.accept()
        self.client.connect((ip_add, 25000))
        print('edge 1 init successfully')
        self.num=0

    def put_d2(self, d2):
        #while self.d2Que.full():
        #    # print('d2 is full')
        #    time.sleep(0.1)
        #    print('算完了但是传不出去啊啊啊啊')
        if self.d2Que.full():
            #print('算完了但是传不出去啊啊啊啊')
            return
        # d2 = d2.detach().numpy()
        # print(d2)
        # print(d2.dtype)
        self.lock.acquire()
        self.d2Que.put(d2)
        self.lock.release()

    def get_img(self):
        while self.imgQue.empty():
            # print('img is empty')
            time.sleep(0.1)
            #print('想获取一个数据去计算但是拿不到啊啊啊啊啊')
        self.lock.acquire()
        img = self.imgQue.get()
        self.lock.release()
        self.num+=1
        # print('2: ', np.sum(img))
        return img

    def recv(self):
        arr = np.zeros(shape=(480, 640, 3), dtype=np.uint8)
        img_sum = np.zeros(shape=(1,), dtype=np.int32)
        cnt = 0
        #while 1:
        #    recv_into(arr, self.client)
        #    recv_into(img_sum, self.client)
        #    if img_sum[0] == np.sum(arr):
        #        cnt += 1
        #    else:
        #        cnt = 0
        #    send_from(np.array([cnt]), self.client)
        #    if cnt >= 5:
        #        break
        while 1:
            if not self.imgQue.full():
                #st=time.time()
                recv_into(arr, self.client)
                #end=time.time()
                #print('trans time: ', end-st)
                img = arr
                img = cv2.resize(img, (width, height))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                if type(img) == np.ndarray and len(img.shape) == 3:  # cv2 image
                    img = torch.from_numpy(img.transpose(2, 0, 1)).float().div(255.0).unsqueeze(0)
                elif type(img) == np.ndarray and len(img.shape) == 4:
                    img = torch.from_numpy(img.transpose(0, 3, 1, 2)).float().div(255.0)
                else:
                    print("unknow image type")
                    exit(-1)
                img = torch.autograd.Variable(img)
                img = img.cuda()
                self.lock.acquire()
                self.imgQue.put(img)
                self.lock.release()
                # print('1: ', np.sum(arr))
            else:
                # print('img is full')
                time.sleep(0.1)
                #print('数据发过来了但是缓冲区满了啊啊啊啊')

    def send(self):
        while 1:
            if not self.d2Que.empty():
                self.lock.acquire()
                d2=self.d2Que.get()
                self.lock.release()
                d2=d2.cpu().detach().numpy()
                send_from(d2, self.a_clinet)
            else:
                # print('d2 is empty')
                time.sleep(0.1)
                #print('算的太慢了没有数据可传啊啊啊啊')

    def num_add(self):
        while 1:
            time.sleep(10)
            print(self.num, 'absbdhgsajdguyas')
            self.num=0

    def run(self):
        _thread.start_new_thread(self.recv, ())
        _thread.start_new_thread(self.send, ())
        _thread.start_new_thread(self.num_add, ())

# def print_time(threadName, delay, counter):
#     while counter:
#         if exitFlag:
#             threadName.exit()
#         time.sleep(delay)
#         print ("%s: %s" % (threadName, time.ctime(time.time())))
#         counter -= 1
