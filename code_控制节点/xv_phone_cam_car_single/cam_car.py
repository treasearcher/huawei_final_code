import time

import cv2
import json
from socket import *
# import socket
import numpy as np
from tool.utils import load_class_names, plot_boxes_cv2
import _thread
import queue
import threading

qsize = 3
boxQue = queue.Queue(qsize)
img_sent = queue.Queue(qsize)
img_recv = queue.Queue(qsize)
last_recv = ''
lock = threading.Lock()
namesfile = 'data/coco.names'
class_names = load_class_names(namesfile)

s = socket(AF_INET, SOCK_STREAM)
s.bind(('', 26000))
s.listen(1)
c,a = s.accept()
print(1)

s = socket(AF_INET, SOCK_STREAM)
s.bind(('', 24999))
s.listen(1)
c_p,a = s.accept()

def recv_from_phone():
    acc_data = b''
    result = b''
    print('recv_rf')
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
        return b''
    img_buffer_numpy = np.frombuffer(result, dtype=np.uint8)  # 将 图片字节码bytes  转换成一维的numpy数组 到缓存中
    img_numpy = cv2.imdecode(img_buffer_numpy, 1)  # 从指定的内存缓存中读取一维numpy数据，并把数据转换(解码)成图像矩阵格式
    img_numpy = cv2.resize(img_numpy, (640, 480))
    # print('img')
    # print(img_numpy.shape)
    return img_numpy

def recv_from_phone_thread():
    global img_recv, last_recv
    while 1:
        img = recv_from_phone()
        if len(img)==0:
            continue
        if img_recv.full():
            lock.acquire()
            last_recv=img
            lock.release()
        else:
            lock.acquire()
            last_recv=''
            img_recv.put(img)
            lock.release()

def get_recv_img():
    global img_recv, last_recv
    while img_recv.empty() and last_recv=='':
        time.sleep(0.1)
    if not img_recv.empty():
        return img_recv.get()
    else:
        img = last_recv
        last_recv=''
        return img


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

fps = 0
fps_dis = 0
def fps_count():
    global fps, fps_dis
    while 1:
        time.sleep(10)
        fps_dis=fps/10
        print(fps)
        fps=0

_thread.start_new_thread(fps_count, ())
_thread.start_new_thread(recv_from_phone_thread, ())
while (1):
    # get a frame
    img = get_recv_img()
    # print(111)

    send_from(img, c)
    # print(222)
    lth = np.zeros(1, dtype=np.int64)
    recv_into(lth, c)
    if not lth[0]==0:
        boxes = np.zeros((1, lth[0], 7), dtype=np.float32)
        recv_into(boxes, c)
        boxes=boxes.tolist()
        for i in range(lth[0]):
            boxes[0][i][-1]=np.int64(boxes[0][i][-1])
        img = plot_boxes_cv2(img, boxes[0], 'predictions.jpg', class_names)
    fps += 1
    img = cv2.putText(img, 'FPS: {}'.format(fps_dis), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
    cv2.imshow('', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
c.close()
s.close()