# -*- coding: utf-8 -*-
import _thread
import queue
import threading
import time
from socket import *

import cv2
import numpy as np

from tool.utils import load_class_names, plot_boxes_cv2

ip_add = '192.168.1.100'
# ip_add = '127.0.0.1'
connect_port = 25003
bind_port = 25000


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


s_3 = socket(AF_INET, SOCK_STREAM)
s_3.bind(('', 28000))
s_3.listen(1)
c_3, _ = s_3.accept()
print('recv')
qsize = 10
recv_que_triple = queue.Queue(qsize)
send_que_triple = queue.Queue(qsize)
lock_triple = threading.Lock()


c_2 = socket(AF_INET, SOCK_STREAM)
c_2.connect((ip_add, connect_port))
print(1)
s = socket(AF_INET, SOCK_STREAM)
s.bind(('', bind_port))
s.listen(3)
print(2)

boxQue = queue.Queue(qsize*20)
img_sent = queue.Queue(qsize*20)
lock = threading.Lock()
# time.sleep(5)

fps = 0
fps_dis = 0

def recv():
    global recv_que_triple
    arr = np.zeros(shape=(480, 640, 3), dtype=np.uint8)
    while 1:
        # print('要收一张图')
        recv_into(arr, c_3)
        # print('收到了一张图')
        if not recv_que_triple.full():
            lock_triple.acquire()
            recv_que_triple.put(arr)
            lock_triple.release()
        # else:
        #     time.sleep(0.1)


def recv_box():
    lth = np.zeros(shape=(1,), dtype=np.int64)
    print(lth[0])
    print("--------------------------------")
    while 1:
        if boxQue.full():
            # print('box is full')
            time.sleep(0.1)
        else:
            # print('要收一个box')
            recv_into(lth, c_2)
            # print('收到了一个box')
            if lth[0] == 0:
                lock.acquire()
                boxQue.put([0])
                lock.release()
                continue
            arr = np.zeros(shape=(1, lth[0], 7), dtype=np.float32)
            recv_into(arr, c_2)
            box = arr.tolist()
            for i in range(lth[0]):
                box[0][i][-1] = np.int64(box[0][i][-1])
            lock.acquire()
            boxQue.put(box)
            lock.release()


# sum_flag = np.zeros(shape=(1,), dtype=np.int32)
# def recv_flag():
#     global sum_flag
#     recv_into(sum_flag, c)
#     print('done')

def cam_send():
    c, a = s.accept()
    # _thread.start_new_thread(recv_flag, ())
    cnt_arr = np.zeros(shape=(1,), dtype=np.int32)
    while 1:
        if recv_que_triple.empty():
            time.sleep(0.1)
            continue
        lock_triple.acquire()
        img = recv_que_triple.get()
        lock_triple.release()
        send_from(img, c)
        send_from(np.array([np.sum(img)]), c)
        recv_into(cnt_arr, c)
        print('发送了一张图')
        if cnt_arr[0] >= 5:
            break
    while 1:
        if recv_que_triple.empty():
            time.sleep(0.1)
            continue
        lock_triple.acquire()
        img = recv_que_triple.get()
        lock_triple.release()
        # print(img)
        send_from(img, c)
        # print('发送了一张图')
        lock.acquire()
        img_sent.put(img)
        lock.release()
        # print(np.sum(img))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def fps_update():
    global fps, fps_dis
    while 1:
        time.sleep(10)
        print(fps)
        fps_dis = fps / 10
        fps = 0


_thread.start_new_thread(recv, ())
_thread.start_new_thread(recv_box, ())
_thread.start_new_thread(cam_send, ())
_thread.start_new_thread(fps_update, ())

# def get_box():
#     while boxQue.empty():
#         time.sleep(0.1)
#     lock.acquire()
#     box = boxQue.get()
#     lock.release()
#     return box

namesfile = 'data/coco.names'
class_names = load_class_names(namesfile)
while (1):
    # get a frame
    while img_sent.empty() or boxQue.empty():
        # print('sent or box are empty')
        time.sleep(0.1)
    lock.acquire()
    img = img_sent.get()
    boxes = boxQue.get()
    lock.release()
    # print(np.sum(img))
    # start = time.time()
    if boxes[0] == 0:
        pass
    else:
        # print('????')
        img = plot_boxes_cv2(img, boxes[0], 'predictions.jpg', class_names)
    img = cv2.putText(img, 'FPS: {}'.format(fps_dis), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
    # end = time.time()
    # print('time: ', end - start)
    cv2.imshow('fps:', img)
    fps += 1
    # send_from(frame, c_3)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
#c.close()
s.close()
