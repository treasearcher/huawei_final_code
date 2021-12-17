import cv2
import json
from socket import *
import queue, _thread, threading, time
import numpy as np


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


server = socket(AF_INET, SOCK_STREAM)
server.bind(('', 24999))
server.listen(1)
c_p, _ = server.accept()
print('trans 1')
client = socket(AF_INET, SOCK_STREAM)
client.connect(('192.168.1.103', 28000))
print('trans 2')
recv_que = queue.Queue(10)
lock = threading.Lock()


def recv_from_phone():
    global recv_que
    arr = np.zeros(shape=(480, 640, 3), dtype=np.uint8)
    cnt=0
    while 1:
        acc_data = b''
        result = b''
        #print('recv_rf')
        while 1:
            acc_data = c_p.recv(1024)
            result += acc_data
            if len(acc_data) == 0 or \
                    (len(acc_data) == 1 and acc_data[0] == 217) or \
                    (len(acc_data) > 1 and acc_data[-1] == 217 and acc_data[-2] == 255):
                break
        if result == b'':
            print(111)
            time.sleep(0.3)
            # return b''
            continue
        img_buffer_numpy = np.frombuffer(result, dtype=np.uint8)  # 将 图片字节码bytes  转换成一维的numpy数组 到缓存中
        img_numpy = cv2.imdecode(img_buffer_numpy, 1)  # 从指定的内存缓存中读取一维numpy数据，并把数据转换(解码)成图像矩阵格式
        img_numpy = cv2.resize(img_numpy, (640, 480))
        lock.acquire()
        recv_que.put(img_numpy)
        lock.release()
        cnt+=1
        print('recv', cnt)


def send():
    global recv_que
    cnt = 0
    while 1:
        if recv_que.empty():
            time.sleep(0.1)
            #print('xiang fa danshi meiyou tu')
            continue
        lock.acquire()
        img = recv_que.get()
        lock.release()
        #print('To send')
        send_from(img, client)
        cnt += 1
        print('send', cnt)


_thread.start_new_thread(recv_from_phone, ())
_thread.start_new_thread(send, ())

while 1:
    time.sleep(10)
